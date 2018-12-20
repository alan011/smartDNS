# smartDNS设计介绍

smartDNS是一套在bind的基础上用django开发的API，将配置数据存在数据库，然后用jinja2语言来渲染模板，自动生成bind的配置文件，自动reload named服务。

这样便可基于这套API做web界面，或者跟其他运维系统做对接，自动添加DNS解析。

smartDNS一般在企业内部网络环境中使用，用于搭建、管理内部DNS。

### 主从架构说明
smartDNS会自动生成bind所需的配置文件，故不再需要bind本身的主从同步机制。

smartDNS中主节点的接口，将接收到有配置变化的请求时（增、删、改请求），会先将数据写入数据库，然后通知所有从节点做一次配置同步。

从节点收到通知后，会自己到数据库中读取数据，在临时目录中生成一套配置文件，并跟原来的配置文件做对比，若有变化则覆盖原来的配置文件，reload named服务（主节点写完数据库后也会做这个操作）。

通过以上机制，便实现了一个dns集群内部的数据同步。
 
### 多个DNS集群数据同步架构说明
smartDNS还支持对多个DNS集群的管理（multi_cluster模式）。

一般一个机房（或者一个区）内部用一套内部DNS，即一个DNS集群，一个主节点，多个从节点。但，如果有多个机房（多个区），就有可能需要用到多个DNS集群。

smartDNS要求在每个集群的主节点（master）上起一个数据库服务，用于存储DNS配置数据。

然后配置其中一个主节点，作为控制中心，通过这个节点的接口来增、删、改、查数据，smartDNS会在多个主节点之间同步数据的修改，保证每个机房数据库中的数据是完全相同的。

不同的集群的配置数据都有集群标签（也可叫IDC标签、或区域标签），各集群的节点在生成bind配置文件时，只会读取自己集群标签的配置数据。

通过这种方式，实现了DNS集群的夸机房管理、数据同步等，也实现了数据备份与多活。

# smartDNS安装部署 

### 安装python3.6
依赖python3.6以上的环境，请安装python3.6+的版本。

### 安装mysql
smartDNS的数据都存在数据库，一般，在smartDNS的主控节点上安装mysql-server即可。
```
~$ yum install mysql-server
~$ chkconfig mysqld on
~$ service mysqld start 
~$ mysqladmin -uroot password '<设置root密码>'      #设置初始密码。
```
注意修改mysql配置文件，默认字符集设置为utf8，不然中文显示会乱：
```
~$ echo "
[mysqld]
datadir=/var/lib/mysql
socket=/var/lib/mysql/mysql.sock
user=mysql
symbolic-links=0
init-connect='SET NAMES utf8'
character-set-server = utf8
[client]
default-character-set=utf8
[mysql]
default-character-set=utf8
[mysqld_safe]
log-error=/var/log/mysqld.log
pid-file=/var/run/mysqld/mysqld.pid
"   >  /etc/my.cnf
~$ service mysqld restart 
```
创建smartDNS需要的库
```
~$ mysql -uroot -p -e 'create database dns_db;'    #创建smartDNS使用的数据库 
```
注意，要在mysql中为其他slave节点创建数据库访问权限。

### 安装smartDNS
创建依赖目录：
```
~$ mkdir -p /var/django_projects/dns
```
从github获取代码后，解压到`/var/django_projects/dns`目录，然后将工程目录改成，`smartDNS`。
然后，安装依赖包：
```
~$ cd /var/django_projects/dns/smartDNS/
~$ pip3 install -r requirements.txt
```
修改数据库配置：
```
~$ vim config/django_settings.py   ### 酌情修改即可。从节点的数据库主机要指到mysql所在的机器上去（一般在主节点上）。
```
修改集群配置：
```
~$ vim config/config.py 
```
配置说明：

1、"cluster config"段：对于主节点，THIS_IS_MASTER设置为True， 从节点设置为False。主节点MASTER_SERVER是一个IP字符串；从节点可以有多台，故，是一个IP列表。

2、“Multi-cluster config”段：若不启用multi_master功能，请将ENABLE_MULTI_CLUSTERS设只为False，忽略其他有关配置项即可。若启用的话，请设置为True，并按照配置文件中的注解仔细配置multi_muster有关的配置项。

3、"Basic config"段：都是关于bind本身的一些配置，一般不用改。

4、“choices for models”段：是一些关于key啊，环境的配置，根据实际情况修改即可。DNS key的制作（也就是那个字符串），请使用dnssec-keygen工具做即可。
