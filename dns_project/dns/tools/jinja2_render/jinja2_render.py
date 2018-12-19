import os
from jinja2 import Template

class Jinja2Render(object):
    """
    To render a file by using jija2.
    """
    def getFileContent(self, file_path):
        if os.path.isfile(file_path):
            f = open(file_path)
            f_content = f.read()
            f.close()
            return {'file_content': f_content}
        else:
            return "ERROR: Jinja2Render.get_file_content(...): File '%s' not exist and cannot be opened."

    def writeTargetFile(self, target_path, file_content):
        target_f = open(target_path, 'w')
        target_f.write(file_content)
        target_f.close()
        return {'result':'SUCCESS'}

    def jinjia2Render(self, data_dict, template_file, target_file):
        ### To get the template file content.
        temp_content = self.getFileContent(template_file)
        # print(temp_content)
        if isinstance(temp_content, str):   ### Means error: file not exist.
            return temp_content

        ### To  render the template with 'data_dict'
        temp_obj = Template(temp_content['file_content'])
        rendered_content = temp_obj.render(**data_dict)
        # print(rendered_content)

        ### To write the target_file
        write_return = self.writeTargetFile(target_file, rendered_content)

        return write_return
