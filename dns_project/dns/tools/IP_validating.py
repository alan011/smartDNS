import socket

def validateIP(address):
    try:
        socket.inet_aton(address)
        return True
    except:
        return False

def validateSubnet(subnet):
    tmp_l = subnet.split('/')
    if len(tmp_l) != 2:
        return False

    if not validateIP(tmp_l[0]):
        return False

    try:
        subnet_mask_len = int(tmp_l[1])
    except:
        return False

    if subnet_mask_len < 0 or subnet_mask_len > 32:
        return False
    return True
    
