#!/usr/local/bin/python

import os, sys
import xlwt
import xlrd
import re
import subprocess
from datetime import datetime

#style_0 = xlwt.easyxf('font: height 240, name Times New Roman')
style_0 = xlwt.easyxf('font: name Times New Roman, height 240, color-index black;' + 
                        'align: horiz left, vertical top;' + 
                        'borders: top thin, bottom thin, left thin, right thin;')
style_1 = xlwt.easyxf('pattern: pattern solid, fore_colour sky_blue;' + 
                        'font: name Times New Roman, height 240, color-index black, bold on;' + 
                        'align: horiz left, vertical top;' + 
                        'borders: top thin, bottom thin, left thin, right thin;')
style_2 = xlwt.easyxf('borders: right thin')
style_6 = xlwt.easyxf('borders: right thin; pattern: pattern solid, fore_colour sky_blue;')  


style_3 = xlwt.easyxf('font: name Times New Roman, height 240, color-index black;' + 
                        'align: horiz left, vertical top;') 
style_4 = xlwt.easyxf('font: name Times New Roman, height 240, color-index black;' + 
                        'align: horiz center, vertical top;') 
style_5 = xlwt.easyxf('pattern: pattern solid, fore_colour sky_blue;' + 
                        'font: name Times New Roman, height 240, color-index black, bold on;' + 
                        'align: horiz center, vertical top;' + 
                        'borders: top thin, bottom thin, left thin, right thin;')


right_arrow = u'\u2192'
down_arrow = u'\u2193'


default_col_width = len("xx.xx.xx.xx.xx") * 256 
g_expand_row = 0
debug = False

def get_style(value, col):
        if col == 0:
                if re.match('[A-Z][A-Z][0-9]+', value): 
                        return style_0 
                else:
                        return style_1 
        else:
                if value == 'firmware version':
                        return style_1 
                else:
                        return style_0 

def get_style2(value):
        if re.match('[0-9a-z]+\.[0-9a-z]+\.[0-9a-z]+\.[0-9a-z]+\.[0-9a-z]+', value): 
                return style_5 
        elif re.match('http', value):
                return style_3
        else:
                return style_4 

def read_max_numbers_of_test_model(sheet):
        flag = 0
        for row in range(sheet.nrows):
                value = sheet.cell_value(row, 0)        
                if flag == 1 and value != "":
                        return (row - begin_row)
                if row == 3:
                        flag = 1
                        begin_row = row

def read_test_model(sheet, col):
        count = 0
        flag = 0 
        for row in range(sheet.nrows):
                value = sheet.cell_value(row, col)        
                if re.match('[A-Z][A-Z][0-9]+', value): 
                        count = count + 1
                        flag = 1 
                        continue
                if flag == 1:
                        return count
        return 0
                        
def get_test_models(pair_list):
        test_models = []
        model = ''

        # ex: ('CC8370-HV', 'CC8370-VVTK-0100a')
        for pair in pair_list:
                if not re.search('_', pair[1]):
                        if re.search('-', pair[0]):
                                name = pair[0].split('-')[0]
                                feature = pair[0].split('-')[1]
                        else:
                                name = pair[0]
                                feature = ''

                        if model == '':
                                model = pair[0]
                        elif model.find(name) >= 0:
                                model = model + '/' + feature 
                        else:
                                test_models.append(model)
                                model = pair[0] 
                
        if model != '':
                test_models.append(model)
        return test_models

def fetch_svn_path():
        p = subprocess.Popen('svn info $PRODUCTDIR', shell=True, stdout = subprocess.PIPE).stdout
        for line in p:
                m = re.match('URL:\s(.+)', line) 
                if m:
                        #print m.group(1)
                        return m.group(1)
        return None 

def insert_new_column(wb_sheet, models, maximum):
        global g_expand_row
        col = 1

        # header rows
        pkg_version = os.getenv('PRODUCTVER') 
        wb_sheet.write(0, col, pkg_version, style_0)

        svn_path = fetch_svn_path() 
        wb_sheet.write(1, col, svn_path, style_0)

        test_type = 'FW'
        wb_sheet.write(2, col, test_type, style_0)

        # test request model rows
        test_list = get_test_models(models)
        if len(test_list) > maximum:
                g_expand_row = len(test_list) - maximum
                maximum = len(test_list)
                #print 'g_expand_row %d' % g_expand_row

        for i in range(maximum):
                if i < len(test_list):
                        wb_sheet.write(3+i, col, test_list[i], style_0)
                else:
                        wb_sheet.write(3+i, col, None, style_0)
                        #break
        
        # model name rows
        model_name_index = 3 + maximum  
        wb_sheet.write(model_name_index, col, 'firmware version', style_1)
        for model in models:
                wb_sheet.write(model_name_index+1, col, model[1], style_0)
                model_name_index = model_name_index + 1


        wb_sheet.col(1).width = len(svn_path) * 256
                
def check_merge(prev_rows, current_rows, row):

        # If first row (pkg version) is not null,
        # the whole column don't need to merge 
        if len(current_rows) != 0 and len(current_rows[0][0]) != 0:
                return False

        value = prev_rows[row][0]

        # Check the left cell, if it's null and don't merge with it 
        #if value == '':
                #return False

        # Only merge with the left cell which is not test model 
        if re.match('[A-Z][A-Z][^-]+-[^-]+$', value): # skip ex:CC8370-HV
                return False
        elif re.match('[A-Z][A-Z][^-]+$', value): # skip ex:VC8201
                return False
        else:
                return True

def check_writable(sheet, row, col):
        if row >= sheet.nrows:
                return True
        if col >= sheet.ncols:
                return True
        if len(sheet.cell_value(row, col)) == 0:
                return True

        return False

def insert_node(read_sheet, write_sheet, trunk, row, col): 

        #svn_path = fetch_svn_path()
        
        # insert node to the trunk 
        if trunk == 'trunk':        
                if check_writable(read_sheet, row + 1, col): 
                        write_sheet.write(row + 1, col, down_arrow, style_4)
                        write_sheet.write(row + 2, col, os.getenv('PRODUCTVER'), style_5)
                return False

        # insert node to the new branch
        elif col == (read_sheet.ncols - 1) and trunk != 'trunk':
                if check_writable(read_sheet, row, col + 1) and check_writable(read_sheet, row - 1, col + 1): 
                        write_sheet.write(row, col + 1, right_arrow, style_4)
                        #write_sheet.write(row - 1, col + 2, svn_path, style_3)
                        write_sheet.write(row, col + 2, os.getenv('PRODUCTVER'), style_5)

                        write_sheet.col(col + 1).width = default_col_width
                        write_sheet.col(col + 2).width = default_col_width
                return False

        # insert node to the new branch 
        # and also adjust the position of other branch (ie. extend the arrow)
        else:
                if check_writable(read_sheet, row, col + 1)  and check_writable(read_sheet, row - 1, col + 1): 
                        write_sheet.write(row, col + 1, right_arrow, style_4)
                        #write_sheet.write(row - 1, col + 2, svn_path, style_3)
                        write_sheet.write(row, col + 2, os.getenv('PRODUCTVER'), style_5)
                        for i in range(read_sheet.nrows):
                                if read_sheet.cell_value(i, col + 1) == right_arrow:
                                        write_sheet.write(i, col + 1, right_arrow, style_4)
                                        write_sheet.write(i, col + 2, right_arrow, style_4)

                        write_sheet.col(col + 1).width = default_col_width
                        write_sheet.col(col + 2).width = default_col_width
                return True 


def gen_pkg_tree(write_sheet):
        info = get_parent_pkg()
        print info
        parent_pkg = info[0] 
        trunk = info[1]
        svn_path = fetch_svn_path() 
        read_sheet = get_support_list(1)
        first_node = True

        # check is the first node or not
        for row in range(read_sheet.nrows):
                if read_sheet.cell_value(row, 2) != '':
                        first_node = False
        # if it's the first node, insert it!
        if first_node:
                write_sheet.write(2, 2, os.getenv('PRODUCTVER'), style_5)
                write_sheet.col(2).width = default_col_width 
                return

        # insert the node 
        #
        # branch_flag and col_add is for adjusting the tree after inserting the node 
        branch_flag = False
        col_add = 0
        parent_svn_path = ''
        for col in range(read_sheet.ncols):
                if branch_flag:
                        col_add = 2

                for row in range(read_sheet.nrows):
                        value = read_sheet.cell_value(row, col)
                        #print repr(value)

                        #if re.match('http', value):
                                #parent_svn_path = value

                        if value == parent_pkg:
                                # insert the node 
                                branch_flag = insert_node(read_sheet, write_sheet, trunk, row, col) 
                                if debug:
                                        print 'parent pkg: %s found!' % value 

                        if len(value) > 0:
                                write_sheet.write(row, col + col_add, value, get_style2(value))

                write_sheet.col(col + col_add).width = default_col_width 

def gen_supportlist_xls(write_sheet):

        read_sheet = get_support_list(0)
        models = get_release_list()
        total_test_models_rows = read_max_numbers_of_test_model(read_sheet)

        #print read_sheet.merged_cells


        # insert the new column
        insert_new_column(write_sheet, models, total_test_models_rows)

        # handle first column 
        # 
        # We must consider the situation that new test models overflow the 'test request model' row 
        # That is g_expand_row > 0, so we need to expand the 'test request model' row
        # 
        col = 0
        max_col_width = 20
        model_length = 0
        test_model_length = 1 
        row_offset = 0
        for row in range(read_sheet.nrows):
                value = read_sheet.cell_value(row, col) 
                if value != '':
                        if g_expand_row != 0 and value == 'model name':
                                for i in range(g_expand_row):
                                        write_sheet.merge(row - 1 + i, row + i, col, col, style_6)
                                write_sheet.write(row + i + 1, col, value, get_style(value, col))
                                row_offset = g_expand_row
                        else:
                                write_sheet.write(row + row_offset, col, value, get_style(value, col))
                else:
                        # merge: r1, r2, c1, c2
                        write_sheet.merge(row-1, row, col, col, style_2)
                        test_model_length = test_model_length + 1

                if len(value) > max_col_width:
                        max_col_width = len(value)

                if re.match('[A-Z][A-Z][0-9]+', value):
                        model_length = model_length + 1

        write_sheet.col(col).width = max_col_width * 256 + 500 

        # expand the 'model name' row
        temp = len(models) - model_length 
        if temp > 0:
                for i in range(temp):
                        value = models[-temp + i][0]
                        write_sheet.write(read_sheet.nrows + i + row_offset, col, value, style_0)



        # traverse all the rows and columns except the first columns 
        max_total_test_models = 0
        prev_rows = []
        for col in range(read_sheet.ncols):
                if col == 0:
                        continue

                max_col_width = 20
                current_rows = []
                for row in range(read_sheet.nrows):
                        value = read_sheet.cell_value(row, col) 

                        # If there are newly added test models and overflow the 'Test request model' row 
                        # The 'Test request model' row should be expand
                        row_offset = check_expand(write_sheet, row, col+1, value, test_model_length)
        

                        # check whether to merge with the left cell 
                        if len(value) == 0 and check_merge(prev_rows, current_rows, row):
                                # merge: r1, r2, c1, c2
                                write_sheet.merge(row + row_offset, row + row_offset, col, col+1, prev_rows[row][1])
                        else:
                                write_sheet.write(row + row_offset, col+1, value, get_style(value, col))

                
                        if len(value) > max_col_width:
                                max_col_width = len(value)

                        # list of tuple
                        current_rows.append((value, get_style(value, col)))                
                
                prev_rows = current_rows

                # adjust column width
                write_sheet.col(col+1).width = max_col_width * 256 




def check_expand(sheet, row, col, value, test_model_length):
        if g_expand_row == 0:
                return 0	
        else:
                magic_row = ((test_model_length + 3) -1)
                if row < magic_row:
                        return 0
                elif row == magic_row: 
                        for i in range(g_expand_row):
                                #print '%d, %d' % (row + 1 +i, col)
                                sheet.write(row + 1 + i, col, "", style_0)
                        return 0 
                else:
                        return g_expand_row
                        



def get_parent_pkg():
        try:
                path = os.path.join(os.getenv('HATHOR'), 'temp', os.getenv('PRODUCTVER'), 'parent_pkg')
                if os.path.exists(path):
                        fh = open(path)
                        parent = fh.readline()
                        parent = re.sub('\n', '', parent)
                        trunk = fh.readline()
                        trunk = re.sub('\n', '', trunk)
                        return (parent, trunk)
                else:

                        print 'The current release pkg version is %s' % os.getenv('PRODUCTVER')
                        print 'What is the \'previous\' release pkg version ?'
                        parent = raw_input()

                        print '\nHathor would generate pkg tree automatically, but we need the information...'
                        print 'Is this new pkg (a)still in the trunk (b)in another new branch ?'
                        choice = raw_input()

                        if choice == 'a':
                                trunk = 'trunk'
                        elif choice == 'b':
                                trunk = 'branch'
                        else:
                                trunk = 'trunk'

        except IOError as e:
                print e
                sys.exit(1)

        return (parent, trunk) 

def parse_release_list(release_list):
        try:
                models = []
                fh = open(release_list)
                line = fh.readline()
                while line:
                        match = re.match(r'([^\s]+)\s+([^\s]+)\s+.+', line)
                        if match:
                                pair = (match.group(1), match.group(2))
                                models.append(pair)
                        line = fh.readline()

        except IOError as e:
                print e
                sys.exit(1)

        return models

def get_release_list():
        if not os.getenv('PRODUCTDIR'):
                print 'Please source devel file first!'
                sys.exit(1)

        release_list = os.path.join(os.getenv('PRODUCTDIR'), 'build', 'settings', os.getenv('PRODUCTVER'), 'release-list')
        release_list_2 = os.path.join(os.getenv('PRODUCTDIR'), 'build', 'release-list')

        if os.path.exists(release_list):
                return parse_release_list(release_list)
        elif os.path.exists(release_list_2):
                return parse_release_list(release_list_2)
        
        print 'Can\'t fetch release-list'
        sys.exit(1)

def get_support_list(sheet_index):
        if not os.getenv('HATHOR'):
                print 'Please execute this script from Hathor!'
                sys.exit(0)

        try:
                path = os.path.join(os.getenv('HATHOR'),'temp',os.getenv('PRODUCTVER'), 'support_list.xls')
                read_wb = xlrd.open_workbook(path)
                read_sheet = read_wb.sheet_by_index(sheet_index)
        except IOError as e:
                print e
                sys.exit(1)

        return read_sheet

if __name__ == '__main__': 

        write_wb = xlwt.Workbook()
        write_sheet = write_wb.add_sheet('sheet1')
        gen_supportlist_xls(write_sheet)

        write_sheet = write_wb.add_sheet('sheet2')  
        gen_pkg_tree(write_sheet)

        write_wb.save('output.xls')

# vim: tabstop=8 shiftwidth=8 softtabstop=8 expandtab
