# -*- coding: utf-8 -*-

# -------------------------------------------------------------------------
#    Copyright (C) 2017-2018 Lukasz G. Migas 
#    <lukasz.migas@manchester.ac.uk> OR <lukas.migas@yahoo.com>
# 
#	 GitHub : https://github.com/lukasz-migas/ORIGAMI
#	 University of Manchester IP : https://www.click2go.umip.com/i/s_w/ORIGAMI.html
#	 Cite : 10.1016/j.ijms.2017.08.014
#
#    This program is free software. Feel free to redistribute it and/or 
#    modify it under the condition you cite and credit the authors whenever 
#    appropriate. 
#    The program is distributed in the hope that it will be useful but is 
#    provided WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE
# -------------------------------------------------------------------------
# __author__ lukasz.g.migas

class PeakAnnotation():
    def __init__(self, **kwargs):
        self.document = kwargs.get("document", "")
        self.dataset = kwargs.get("dataset", "")
        
    def get_document_annotations(self):
        pass
    
    def get_annotation(self):
        pass
    
    def set_document_annotations(self):
        pass
    
    def set_annotation(self):
        pass
    
    def add_annotation(self, annotation_dict, **kwargs):
        pass
    
    