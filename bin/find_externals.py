######################################################################
# This file is mainly to find the svn external files 
# So that we can avoid setting svn executable property to external files 
######################################################################
import os, sys
import subprocess
import re

class ExternalFile:

    hathor_path = os.getenv('HATHOR')
    svn_pg_file = os.getenv('HATHOR_METADATA_SVN_PG')
    args_for_find_file = os.getenv('HATHOR_METADATA_ARGS_FOR_FIND') 
    is_onefw = os.getenv('ISONEFW')
    product_dir = os.getenv('PRODUCTDIR')
    #print is_onefw
    #print product_dir

    def __init__(self):

        if self.svn_pg_file != None and os.path.exists(self.svn_pg_file):
            os.remove(self.svn_pg_file)
        if self.args_for_find_file != None and os.path.exists(self.args_for_find_file):
            os.remove(self.args_for_find_file)

    def get_svnpg(self):

        os.chdir(self.product_dir)
        #print self.is_onefw
        if self.is_onefw == 'true':
            cmd = self.hathor_path + '/bin/svnpg > ' + self.svn_pg_file    
        else:
            cmd = 'svn pg svn:externals . -R > ' + self.svn_pg_file    
        #print cmd
        os.system(cmd)
        os.chdir(self.hathor_path)

    def parse_svnpg(self):

        args = ''
        if self.svn_pg_file != None and os.path.exists(self.svn_pg_file):
            try:
                fh = open(self.svn_pg_file)
                line = fh.readline()

                while line:
                    # skip null line
                    if line.strip(): 
                        if re.search(' - ', line): 
                            ext_dir = re.split(' ', line) 
                            if re.search('^\.', ext_dir[0]):
                                parent_dir = ext_dir[0] 
                            else:
                                parent_dir = './' + ext_dir[0]

                            if re.search('http://', ext_dir[2]):
                               args = args + ' -or -path ' + parent_dir + '/' + ext_dir[3]    
                            else:
                               args = args + ' -or -path ' + parent_dir + '/' + ext_dir[2]    
                        else:
                            ext_dir = re.split(' ', line) 
                            if re.search('http://', ext_dir[0]):
                               args = args + ' -or -path ' + parent_dir + '/' + ext_dir[1]    
                            else:
                               args = args + ' -or -path ' + parent_dir + '/' + ext_dir[0]    

                    line = fh.readline()
            except IOError as e:
                print e
            fh.close()

        #print args
        out = open(self.args_for_find_file, 'w')
        out.write(args)
        out.close()
    
      
if __name__ == '__main__':
    ext = ExternalFile()    
    ext.get_svnpg()
    ext.parse_svnpg()

# vim: tabstop=4 shiftwidth=4 softtabstop=4 expandtab
