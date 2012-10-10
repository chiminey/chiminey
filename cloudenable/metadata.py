# -*- coding: utf-8 -*-
#
# Copyright (c) 2011-2012, RMIT e-Research Office
#   (RMIT University, Australia)
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the RMIT, the RMIT members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""
metadata.py

.. moduleauthor:: Ian Thomas <Ian.Edward.Thomas@rmit.edu.au>
based on hpctardis.googlecode.com commit: edb6cbac1a87

"""
from os import path
import re
import itertools
import logging
import logging.config



logger = logging.getLogger('metadata')

number = "[+-]?((\d+)(\.\d*)?)|(\d+\.\d+)([eE][+-]?[0-9]+)?"



rulesets = {
            #: This ruleset will produce a Schema entry called "general 1.0" in the namespace
            #: 'http://tardis.edu.au/schemas/general/1'
            ('http://tardis.edu.au/schemas/general/1','general 1.0'):
                #  This rule matches any files matching metadata\..* filenames and will extract
                # to a parmeter called project.
                (('Project',("metadata\..*$",),
                    # call the get_file_regex function, which returns back (value,unit) tuple.
                    # get_file_regex function finds first line of file that has Project followed
                    # by arbitrary characters. These characters are matched into value group
                    # and unit group is empty in this case.
                    "get_file_regex(context,'Project~\s+(?P<value>.+)(?P<unit>)',False)"),

                # This rule matches HPC output files which have a dot followed by o in them
                ('Number Of CPUs',("^.*[_0-9]*\.o(\d+)$",),
                    "get_file_regex(context,'Number of cpus:\s+(?P<value>.+)(?P<unit>)',True)"),
                ('Maximum virtual memory',("^.*[_0-9]*\.o(\d+)$",),
                    "get_file_regex(context,'Max virtual memory:\s+(?P<value>[0-9]+)(?P<unit>(M|G|K)B)',True)"),
                ('Max jobfs disk use',("^.*[_0-9]*\.o(\d+)$",),
                    "get_file_regex(context,'Max jobfs disk use:\s+(?P<value>.*)(?P<unit>(M|G|K)B)',True)"),
                ('Walltime',("^.*[_0-9]*\.o(\d+)$",),
                    # True below indicates that if multiple files in dataset match file regex, then choose
                    # the one of the largest value in filename suffix number
                    "get_file_regex(context,'Elapsed time:\s+(?P<value>[\w:]+)(?P<unit>)',True)")
             ),
            # This schema captures specific information for VASP output
            ('http://tardis.edu.au/schemas/vasp/1','vasp 1.0'):
                # The presense of KPOINTS files in dataset triggers creaton of this schema. Note
                # That if tardis ingests the same file multiple times, it adds number prefix
                # as above, so all patterns should account for this in the regex.
                (('kpoint_grid',("KPOINTS[_0-9]*",),
                    # slurp the KPOINT file, then get the relative linenumber
                    "get_file_line(context,-3)"),
                ('kpoint_grid_offset',("KPOINTS[_0-9]*",),
                    "get_file_line(context,-2)"),
                # TODO: remove number as can cause bad matches
                ('ENCUT',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'\s+ENCUT\s*=\s*(?P<value>%s)\s+(?P<unit>eV)',False)" % number),
                ('NIONS',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'\s+NIONS\s*\=\s*(?P<value>%s)(?P<unit>)',False)" % number),
                ('NELECT',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'\s+NELECT\s*\=\s*(?P<value>%s)\s+(?P<unit>.*)$',False)" % number),
                ('ISIF',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'\s+ISIF\s+\=\s+(?P<value>%s)\s+(?P<unit>.*)$',False)" % number),
                ('ISPIN',("OUTCAR[0-9]*",),
                    "get_file_regex(context,'\s+ISPIN\s+\=\s+(?P<value>%s)\s+(?P<unit>.*)$',False)" % number),
                ('NSW',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'NSW\s*\=\s*(?P<value>%s)\s*(?P<unit>.*)$',False)" % number),
                ('IBRION',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'IBRION\s*\=\s*(?P<value>%s)\s+(?P<unit>.*)$',False)" % number),
                ('ISMEAR',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'ISMEAR\s*\=\s*(?P<value>%s)(?P<unit>)',False)" % number),
                ('POTIM',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'POTIM\s*\=\s*(?P<value>%s)(?P<unit>)',False)" % number),
                #('MAGMOM',("POSCAR[_0-9]*",),
                    #"get_file_lines(context,1,4)"),
                ('Descriptor Line',("INCAR[_0-9]*",),
                    "get_file_regex(context,'System = (?P<value>.*)(?P<unit>)',False)"),
                ('EDIFF',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'EDIFF\s*\=\s*(?P<value>[^\s]+)(?P<unit>)',False)"),
                ('EDIFFG',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'EDIFFG\s*\=\s*(?P<value>[^\s]+)(?P<unit>)',False)"),
                ('NELM',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'NELM\s*\=\s*(?P<value>[^;\s]+)(?P<unit>)',False)"),
                ('ISTART',("INCAR[_0-9]*",),
                    "get_file_regex(context,'ISTART\s*\=\s*(?P<value>[^;\s]+)(?P<unit>)',False)"),
                ('TEBEG',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'TEBEG\s*\=\s*(?P<value>[^;\s]+)(?P<unit>)',False)"),
                ('TEEND',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'TEEND\s*\=\s*(?P<value>[^;\s]+)(?P<unit>.*)',False)"),
                ('SMASS',("OUTCAR[_0-9]*",),
                    "get_file_regex(context,'SMASS\s*\=\s*(?P<value>[^\s]+)(?P<unit>.*)',False)"),
                ('Final Iteration',("OSZICAR[_0-9]*",),
                    "get_final_iteration(context)"),
                ('TITEL',("OUTCAR[_0-9]*",),
                    # find all lines which match regex and into multiline string
                    "('\\n '.join(get_file_regex_all(context,'TITEL\s+\=\s+(?P<value>.*)$')),'')"),
                ('LEXCH',("OUTCAR[_0-9]*",),
                    "('\\n '.join(get_file_regex_all(context,'LEXCH\s+\=\s+(?P<value>[^\s]+)')),'')"),
                ('Cell Scaling',("POSCAR[_0-9]*",),
                    "get_file_line(context,1)"),
                ('Cell Parameter1',("POSCAR[_0-9]*",),
                    "get_file_line(context,2)"),
                ('Cell Parameter2',("POSCAR[_0-9]*",),
                    "get_file_line(context,3)"),
                ('Cell Parameter3',("POSCAR[_0-9]*",),
                    "get_file_line(context,4)")
             ),

            ('http://tardis.edu.au/schemas/siesta/1','siesta 1.0'):
                (('SystemName',("input[_0-9]*\.fdf",),
                    "get_file_regex(context,'SystemName\s+(?P<value>.*)(?P<unit>)',False)"),
                ('MeshCutoff',("input[_0-9]*\.fdf",),
                    "get_file_regex(context,'MeshCutoff\s+(?P<value>[^\s]+)(?P<unit>.*)',False)"),
                ('ElectronicTemperature',("input[_0-9]*\.fdf",),
                    "get_file_regex(context,'ElectronicTemperature\s+(?P<value>[^\s]+)(?P<unit>.*)',False)"),
                #('k-grid',("input\.fdf",),
                #   "get_regex_lines(context,'\%block k_grid_Monkhorst_Pack','\%endblock k_grid_Monkhorst_Pack')"),
                ('k-grid',("input[_0-9]*\.fdf",),
                    "get_regex_lines(context,'\%block kgridMonkhorstPack','\%endblock kgridMonkhorstPack')"),
                ('PAO.Basis',("input[_0-9]*\.fdf",),
                    # return all lines between the first and second regex
                    "get_regex_lines(context,'\%block PAO.Basis','\%endblock PAO.Basis')"),
                ('MD.TypeOfRun',('input[_0-9]*\.fdf',),
                    "get_file_regex(context,'(?<!\#)MD\.TypeOfRun\s+(?P<value>.*)(?P<unit>)',False)"),
                ('MD.NumCGsteps',('input[_0-9]*\.fdf',),
                    "get_file_regex(context,'(?<!\#)MD\.NumCGsteps\s+(?P<value>[^\s]+)(?P<unit>)',False)"),
                ('iscf',('output[_0-9]*',),
                    "(get_regex_lines_vallist(context,'siesta\:\siscf','^$')[-1],'')"),
                ('E_KS',('output[_0-9]*',),
                    "get_file_regex(context,'^siesta:\s+E\_KS\(eV\)\s+\=\s+(?P<value>.*)(?P<unit>)',False)"),
                ('Occupation Function',('input[_0-9]*\.fdf',),
                    "get_file_regex(context,'(?<!\#)OccupationFunction\s+(?P<value>.*)(?P<unit>)',False)"),
                ('OccupationMPOrder',('input[_0-9]*\.fdf',),
                    "get_file_regex(context,'(?<!\#)OccupationMPOrder\s+(?P<value>.*)(?P<unit>)',False)"),
                ('MD.MaxForceTol',('input[_0-9]*\.fdf',),
                    "get_file_regex(context,'(?<!\#)MD\.MaxForceTol\s+(?P<value>[^\s]+)\s+(?P<unit>.*)',False)")
             ),

            ('http://tardis.edu.au/schemas/gulp/1','gulp 1.0'):
                (('Run Type',("optiexample[_0-9]*\.gin",),
                    "(get_file_line(context,0)[0].split(' ')[0],'')"),
                ('Run Keyword',("optiexample[_0-9]*\.gin",),
                    "(' '.join(get_file_line(context,0)[0].split(' ')[1:]).rstrip(),'')"),
                ('Library',("optiexample[_0-9]*\.gin",),
                    "(get_file_regex(context,'(?<!\#)library\s+(?P<value>.*)(?P<unit>)',False)[0].rstrip(),'')"),
                ('CoordinateFile',("optiexample[_0-9]*\.gin",),
                    # This is just python: get two matching strings, reverse them and joint into string with dot between.
                    "('.'.join(get_file_regex(context,'(?<!\#)output\s+(?P<value>\S+)\s+(?P<unit>\S+)',False)[::-1]),'')"),
                ('Formula',("optiexample[_0-9]*\.gout",),
                    # strip may be needed to remove leading newlines from strings
                    "(get_file_regex(context,'(?<!\#)\s*Formula\s+\=\s+(?P<value>.*)(?P<unit>)',False)[0].strip(),'')"),
                ('Total number atoms/shell',("optiexample[_0-9]*\.gout",),
                    "(get_file_regex(context,'(?<!\#)\s*Total number atoms\/shells\s+\=\s+(?P<value>.*)(?P<unit>)',False)[0].strip(),'')")
            ),

           ('http://tardis.edu.au/schemas/gulp/2','gulp2 1.0'):
                (('Run Type',("mdexample[_0-9]*\.gin",),
                   "(get_file_regex(context,'(?<!#)(?P<value>\w+)\s+(?P<unit>\w+)',False)[0],'')"),
                ('Run Keyword',("mdexample[_0-9]*\.gin",),
                   "(' '.join(get_file_regex(context,'(?<!#)(?P<value>\w+)\s+(?P<unit>\w+)',False)[1:]).rstrip(),'')"),
                ('Library',("mdexample[_0-9]*\.gin",),
                    "(get_file_regex(context,'(?<!\#)library\s+(?P<value>.*)(?P<unit>)',False)[0].rstrip(),'')"),
                ('Formula',("mdexample[_0-9]*\.gout",),
                   "(get_file_regex(context,'(?<!\#)\s*Formula\s+\=\s+(?P<value>.*)(?P<unit>)',False)[0].strip(),'')")
            ),

            ('http://tardis.edu.au/schemas/crystal/1','crystal 1.0'):
                (('Experiment name',("INPUT[_0-9]*",),
                    "get_file_line(context,0)"),
                ('Calculation type',("INPUT[_0-9]*",),
                    "get_file_line(context,1)"),
                ('Space/layer/rod/point group',("INPUT[_0-9]*",),
                    "get_file_line(context,3) if (get_file_line(context,1)[0].strip() == 'CRYSTAL') else get_file_line(context,2)"),
                ('Lattice parameter',("INPUT[_0-9]*",),
                    "get_file_line(context,4) if (get_file_line(context,1)[0].strip() == 'CRYSTAL') else get_file_line(context,3)"),
                ('SLABCUT',("INPUT[_0-9]*",),
                    "('yes','') if (get_file_regex(context,'^(?P<value>SLABCUT)(?P<unit>)',False)[0].strip() == 'SLABCUT') else ('no','')"),
                ('OPTGEOM',("INPUT[_0-9]*",),
                    "('yes','') if (get_file_regex(context,'^(?P<value>OPTGEOM)(?P<unit>)',False)[0].strip() == 'OPTGEOM') else ('no','')"),
                ('TESTGEOM',("INPUT[_0-9]*",),
                    "('yes','') if (get_file_regex(context,'^(?P<value>TESTGEOM)(?P<unit>)',False)[0].strip() == 'TESTGEOM') else ('no','')"),
                ('UHF',("INPUT[_0-9]*",),
                    "('yes','') if (get_file_regex(context,'^(?P<value>UHF)(?P<unit>)',False)[0].strip() == 'UHF') else ('no','')"),
                ('DFT',("INPUT[_0-9]*",),
                    "('yes','') if (get_file_regex(context,'^(?P<value>DFT)(?P<unit>)',False)[0].strip() == 'DFT') else ('no','')"),
                ('SHRINK',("INPUT[_0-9]*",),
                    "(get_file_regex(context,'^(?P<value>SHRINK)(?P<unit>)',False,nextline=True)[0].strip(),'')"),
                ('MAXCYCLE',("INPUT[_0-9]*",),
                    "(get_file_regex(context,'^(?P<value>MAXCYCLE)(?P<unit>)',False,nextline=True)[0].strip(),'')"),
                ('FMIXING',("INPUT[_0-9]*",),
                    "(get_file_regex(context,'^(?P<value>FMIXING)(?P<unit>)',False,nextline=True)[0].strip(),'')"),
                ('BROYDEN',("INPUT[_0-9]*",),
                    "(get_file_regex(context,'^(?P<value>BROYDEN)(?P<unit>)',False,nextline=True)[0].strip(),'')")
            ),

            ('http://tardis.edu.au/schemas/test/1',''):
                (('Test',("R-2-2.tif",),
                    "get_constant(context,'99','foobars')"),
                ('Test2',("R-2-2.tif","R-2-5.tif"),
                     "get_constant(context,'hello','')")
            )
        }


def _get_file_handle(context, full_fname):
    logger.debug("get file handle = %s" % full_fname)
    file_handle = open(full_fname, "r")
    return file_handle


def get_final_iteration(context):
    """ Returns the final iteration number from a VASP run

        :param context: package of parameter data
        :returns: value unit tuple
    """
    fileregex = context['fileregex'][0]
    filename = _get_file_from_regex(fileregex, context['ready'], False)
    logger.debug("filename=%s" % filename)
    if not filename or filename not in context['ready']:
        logger.debug("found None")
        return ("", "")
    else:
        logger.debug("found ready %s" % filename)
        try:
            fp = _get_file_handle(context, context['ready'][filename])
        except Exception:
            return ("", "")
        if fp:
            regex = "RMM\:\s*(?P<value>\d+)\s*"
            regx = re.compile(regex)
            max_value = 0
            for line in fp:
                logger.debug("line=%s" % line)
                match = regx.search(line)
                if match:
                    val = match.group('value')
                    try:
                        value = int(val)
                    except ValueError:
                        value = 0
                    logger.debug("value=%s" % value)
                    if value > max_value:
                        max_value = value
            fp.close()
            logger.debug("max_value = %s" % max_value)
            return (str(max_value), "")
        else:
            return ("", "")


def _get_file_from_regex(regex,context, return_max):
    """Returns the single key from ready dict which matches the regex.
    If return_max, then only use file which the largest group match in regex
    """
    regx = re.compile(regex)
    logger.debug("return_max=%s" % return_max)
    key = None
    max_match = ""
    max_value = 0
    logger.debug("regex=%s" % regex)
    for key in dict(context):
        logger.debug("key=%s" % key)
        match = regx.match(key)
        logger.debug("match=%s" % match)
        if return_max:
            logger.debug("return_max")
            if match:
                logger.debug("match=%s" % match)
                matched_groups = match.groups()
                if matched_groups:
                    if len(matched_groups) == 1:
                        if matched_groups[0] > max_value:
                            max_match = key
                            max_value = matched_groups[0]
        else:
            if match:
                logger.debug("matched to %s" % str(match.group(0)))
                return match.group(0)

    logger.debug("max_match=%s" % max_match)
    return max_match


def get_file_lines(context, linestart,lineend):
    """ Returns the content of file in the line range.
        Returns no unit value and only works for smallish local files

        :param context: package of parameter data
        :param linestart: the begin of the range of lines to extract
        :param lineend: the end of the range of lines to extract
        :returns: value unit tuple, where value is newline separated string
    """
    # match fileregex to available files
    #regx = re.compile(fileregex)
    #filename = None
    #for key in context['ready']:
    #    match = regx.match(key)
    #    if match:
    #        filename = key
    #        break
    fileregex = context['fileregex'][0]
    filename = _get_file_from_regex(fileregex, context['ready'], False)
    if filename not in context['ready']:
        return (None, '')
    else:

        try:
            fp = _get_file_handle(context, context['ready'][filename])
        except Exception:
            return ('', '')
        if fp:
            res = []
            for i, line in enumerate(fp):
                if i in range(linestart, lineend):
                    res.append(line)

            return ("\n".join(res), '')
    return ('', '')


def get_file_line(context,lineno):
    """ Returns the content of relative linenumber.
        Assumes no unit value and only works for smallish files

        :param context: package of parameter data
        :param lineno: the line number of the file to extract
        :returns: value unit tuple
    """

    # match fileregex to available files
    #regx = re.compile(fileregex)
    #filename = None
    #for key in context['ready']:
        #match = regx.match(key)
        #if match:
            #filename = key
            #break
    fileregex = context['fileregex'][0]

    filename = _get_file_from_regex(fileregex, context['ready'], False)
    if filename not in context['ready']:
        return (None, '')
    else:
        #import pdb; pdb.set_trace()
        try:
            fp = _get_file_handle(context, context['ready'][filename])
        except Exception:
            return ("", "")
        if fp:
            line_list = fp.readlines()
            fp.close()
            logger.debug(line_list)
            return (str(line_list[lineno]), '')
    return ('', '')


def get_regex_lines(context, startregex,endregex):
    """ Returns the file content of lines that match between two matching
        regular expressions.

        Returns blank unit value and only works for smallish files

        :param context: package of parameter data
        :param startregex: starting regex for extraction
        :param endregex: ending regex for extraction
        :returns: value unit tuple
    """
    fileregex = context['fileregex'][0]

    filename = _get_file_from_regex(fileregex, context['ready'], False)

    if not filename or filename not in context['ready']:
        logger.debug("found None")
        return ('', '')
    else:
        logger.debug("foobar=%s" % context['ready'][filename])

        try:
            fp = _get_file_handle(context, context['ready'][filename])
        except Exception:
            return ('', '')
        if fp:
            startreg = re.compile(startregex)
            endreg = re.compile(endregex)
            res = []
            in_region = False
            for line in fp:
                start_match = startreg.search(line)
                end_match = endreg.search(line)
                if start_match:
                    in_region = True
                    continue
                if end_match:
                    in_region = False
                    continue
                if in_region:
                    res.append(line)
            fp.close()
        return ("".join(res), '')




def get_regex_lines_vallist(context, startregex, endregex):
    """ Returns the file content of lines that match between two matching
        regular expressions as a list of lines

        :param context: package of parameter data
        :param startregex: starting regex for extraction
        :param endregex: ending regex for extraction
        :returns: list of strings
    """

    fileregex = context['fileregex'][0]

    filename = _get_file_from_regex(fileregex, context['ready'], False)

    if not filename or filename not in context['ready']:
        logger.debug("found None")
        return ['']
    else:

        try:
            fp = _get_file_handle(context, context['ready'][filename])
        except Exception:
            return ['']
        if fp:
            startreg = re.compile(startregex)
            endreg = re.compile(endregex)
            res = []
            in_region = False
            for line in fp:
                start_match = startreg.search(line)
                end_match = endreg.search(line)
                if start_match:
                    in_region = True
                    continue
                if end_match:
                    in_region = False
                    continue
                if in_region:
                    res.append(line)
            fp.close()
        return res



def get_file_regex(context, regex, return_max, **kwargs):
    """ Returns the content of the file that matches regex as value, unit pair

        :param context: package of parameter data
        :param regex: regex with named groups value and unit
        :param return_max: if true, context filename regex must contain single group.  If multiple files match this group, then only one with largest numeric is used.
        :param kwargs: if 'nextline' in kwargs and true then return whole line after matching regex
        :returns: value unit tuple
    """

    # match fileregex to available files
    #regx = re.compile(fileregex)
    #filename = None
    #for key in context['ready']:
    #    match = regx.match(key)
    #    if match:
    #        filename = key
    #        break

    # FIXME: only handles single file pattern
    fileregex = context['fileregex'][0]
    filename = _get_file_from_regex(fileregex, context['ready'], return_max)

    if not filename or filename not in context['ready']:
        logger.debug("found None")
        return ('', '')
    else:
        try:
            fp = _get_file_handle(context, context['ready'][filename])
        except Exception, e:
            logger.error("problem with filehandle %s" % e)
            return ('', '')
        if fp:
            regx = re.compile(regex)
            for line in fp:
                match = regx.search(line)

                if match:
                    value = match.group('value')
                    unit = str(match.group('unit'))
                    if not unit:
                        unit = ''
                    logger.debug("value=%s unit=%s" % (value, unit))

                    if 'nextline' in kwargs and kwargs['nextline']:
                        next_line = fp.next()
                        res = (next_line, '')
                        fp.close()
                        return res
                    else:
                        fp.close()
                        res = (value, unit)
                        for g in res:
                            logger.debug("final matched %s" % g)
                        return res
        else:
            logger.debug("no filehandle")
        fp.close()
        return ('', '')




def get_file_regex_all(context,regex):
    """ Returns the content of the file that matches regex as a list of
        value, unit pairs

        :param context: package of parameter data
        :param regex: regex with named groups value and unit
        :returns: list of <value,unit> tuples
    """

    # match fileregex to available files
    #regx = re.compile(fileregex)
    #filename = None
    #for key in context['ready']:
    #    match = regx.match(key)
    #    if match:
    #        filename = key
    #        break

    # FIXME: only handles single file pattern
    logger.debug("get_file_regex_all")
    fileregex = context['fileregex'][0]
    logger.debug("fileregex=%s" % fileregex)
    filename = _get_file_from_regex(fileregex, context['ready'], False)
    logger.debug("filename=%s" % filename)

    final_res = []
    if not filename or filename not in context['ready']:
        logger.debug("found None")
        return []
    else:
        try:
            fp = _get_file_handle(context, context['ready'][filename])
        except Exception:
            logger.error("bad file handle")
            return []
        if fp:
            regx = re.compile(regex)
            for line in fp:
                match = regx.search(line)

                if match:
                    value = match.group('value')
                    logger.debug("value=%s" % value)
                    final_res.append(value.rstrip())
            fp.close()
        logger.debug("final_res=%s" % final_res)
        return final_res


def get_constant(context,val,unit):
    """ Create a constant value unit pair

        :param val: value of the constant
        :param unit: the unit of the constant
        :returns: value unit tuple
    """
    return (val,unit)


aux_functions = {
                              "get_file_line":get_file_line,
                              "get_file_lines":get_file_lines,
                              "get_file_regex":get_file_regex,
                              "get_file_regex_all":get_file_regex_all,
                              "get_regex_lines":get_regex_lines,
                              "get_regex_lines_vallist":get_regex_lines_vallist,
                              "get_final_iteration":get_final_iteration,
                              "get_constant":get_constant}




def process_datafile(fname, full_fname, ruleset):
    """Extract metadata using given rules on a specific datafile

        :param datafile: the file to analyse
        :param ruleset: the set of rules to use
        :returns: the metadata extracted
    """
    from collections import defaultdict
    ready = defaultdict()
    meta = {}

    #logger.debug("ready=%s\n" % ready)
    try:

        regex_cache = {}
        ready[fname] = full_fname # ugh!
        for tagname, file_patterns, code in ruleset:
            #logger.debug("file_patterns=%s,code=%s\n" % (file_patterns,code))

            # check whether we have all files available.
            # f could have _number regex
            # This is a potential performance bottleneck
            count = 0
            for file_pattern in file_patterns:
                # cache the reges
                if file_pattern in regex_cache:
                    rule_file_regx = regex_cache[file_pattern]
                else:
                    rule_file_regx = re.compile(file_pattern)
                    regex_cache[file_pattern] = rule_file_regx
                filename = None
                for datafilename in ready:
                        match = rule_file_regx.match(datafilename)
                        if match:
                            #logger.debug("matched % s" % datafilename)
                            filename = datafilename
                            break
                        else:
                            pass
                            #logger.debug("no match to %s" % datafilename)
                #logger.debug("filename=%s\n" % filename)

                if filename in ready:
                    count += 1

            if count == len(file_patterns):
                logger.debug("ready")
                data_context = {'ready': ready,
                                'fileregex': file_patterns}
                logger.debug("data_context=%s" % data_context)

                aux_context = aux_functions
                aux_context['context'] = data_context
                try:
                    (value, unit) = eval(code, {}, aux_context)
                except Exception, e:
                    logger.error("Exception %s" % e)
                    logger.debug("value,unit=%s %s" % (value, unit))

                meta[tagname] = (value, unit)
    except ValueError:
        logger.error("ruleset = %s" % ruleset )
        raise

    return meta

def process_all(local_dir):
    import os
    res = {}
    for (dirpath, dirnames, filenames) in os.walk(local_dir):
        for fname in filenames:
            full_fname = os.path.join(dirpath, fname)
            #logger.debug("full_fname=%s" % full_fname)
            metadata_set = {}
            for schemainfo in rulesets:
                meta = process_datafile(fname, full_fname, rulesets[schemainfo])
                #print "meta=%s" % meta
                if meta:
                    metadata_set["%s # %s" % schemainfo] = meta
                #metadata_set.update(meta)
            if metadata_set:
                res[full_fname] = metadata_set
            #print full_fname , metadata_set

    return res
if __name__ == '__main__':
    logging.config.fileConfig('logging.conf')
    import time
    path = "./testing/dataset1"
    begins = time.time()
    res = process_all(path)
    import json
    print json.dumps(res,indent=1)
    ends = time.time()
    logger.info("Total execution time: %d seconds" % (ends-begins))

