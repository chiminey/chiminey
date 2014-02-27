# Copyright (C) 2014, RMIT University

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
import os
import json
import logging

from chiminey import storage
from chiminey import mytardis
from chiminey.corestages import Transform


logger = logging.getLogger(__name__)


class VASPTransform(Transform):

    OUTCAR_FILE = "OUTCAR"
    VALUES_FNAME = "values"

    def curate_dataset(self, run_settings, experiment_id, base_dir, output_url,
        all_settings):

        logger.debug("output_url=%s" % output_url)

        outcar_url = storage.get_url_with_credentials(all_settings,
            os.path.join(output_url, self.OUTCAR_FILE), is_relative_path=False)
        logger.debug("outcar_url=%s" % outcar_url)

        try:
            outcar_content = storage.get_file(outcar_url)
        except IOError, e:
            logger.error(e)
            toten = None
        else:
            toten = None
            for line in outcar_content.split('\n'):
                #logger.debug("line=%s" % line)
                if 'e  en' in line:
                    logger.debug("found")
                    try:
                        toten = float(line.rsplit(' ', 2)[-2])
                    except ValueError, e:
                        logger.error(e)
                        pass
                    break

        logger.debug("toten=%s" % toten)

        values_url = storage.get_url_with_credentials(all_settings,
            '%s%s' % (output_url, self.VALUES_FNAME), is_relative_path=False)
        logger.debug("values_url=%s" % values_url)

        try:
            values_content = storage.get_file(values_url)
        except IOError, e:
            logger.error(e)
            values = None
        else:
            values = None
            try:
                values = dict(json.loads(values_content))
            except Exception, e:
                logger.error(e)
                pass
        logger.debug("values=%s" % values)

        # FIXME: all values from map are strings initially, so need to know
        # type to coerce.
        num_kp = None
        if 'num_kp' in values:
            try:
                num_kp = int(values['num_kp'])
            except IndexError:
                pass
            except ValueError:
                pass

        logger.debug("num_kp=%s" % num_kp)

        encut = None
        if 'encut' in values:
            try:
                encut = int(values['encut'])
            except IndexError:
                pass
            except ValueError:
                pass
        logger.debug("encut=%s" % encut)

        def _get_exp_name_for_vasp(settings, url, path):
            """
            Break path based on EXP_DATASET_NAME_SPLIT
            """
            return str(os.sep.join(path.split(os.sep)[-2:-1]))

        def _get_dataset_name_for_vasp(settings, url, path):
            """
            Break path based on EXP_DATASET_NAME_SPLIT
            """
            encut = settings['ENCUT']
            numkp = settings['NUMKP']
            runcounter = settings['RUNCOUNTER']
            return "%s:encut=%s,num_kp=%s" % (runcounter, encut, numkp)
            #return str(os.sep.join(path.split(os.sep)[-EXP_DATASET_NAME_SPLIT:]))

        all_settings['ENCUT'] = encut
        all_settings['NUMKP'] = num_kp
        all_settings['RUNCOUNTER'] = all_settings['contextid']

        experiment_id = mytardis.create_dataset(
            settings=all_settings,
            source_url=output_url,
            exp_id=experiment_id,
            exp_name=_get_exp_name_for_vasp,
            dataset_name=_get_dataset_name_for_vasp,
            dataset_paramset=[
                mytardis.create_paramset("remotemake/output", []),
                mytardis.create_graph_paramset("dsetgraph",
                    name="makedset",
                    graph_info={},
                    value_dict={"makedset/num_kp": num_kp, "makedset/encut": encut, "makedset/toten": toten}
                        if (num_kp is not None)
                            and (encut is not None)
                            and (toten is not None) else {},
                    value_keys=[]
                    ),
                ]
            )

        return experiment_id

