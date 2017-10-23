# -*- coding: utf-8
# pylint: disable=line-too-long
"""Module to deal with HDF5 files"""

import time
import numpy as np

import anvio
import anvio.db as db
import anvio.tables as t
import anvio.utils as utils
import anvio.terminal as terminal
import anvio.constants as constants
import anvio.filesnpaths as filesnpaths

from anvio.errors import HDF5Error, AuxiliaryDataError


__author__ = "A. Murat Eren"
__copyright__ = "Copyright 2015, The anvio Project"
__credits__ = []
__license__ = "GPL 3.0"
__maintainer__ = "A. Murat Eren"
__email__ = "a.murat.eren@gmail.com"


run = terminal.Run()
progress = terminal.Progress()
pp = terminal.pretty_print

class AuxiliaryDataForSplitCoverages(object):
    def __init__(self, file_path, db_hash, create_new=False, ignore_hash=False, run=run, progress=progress, quiet=False):
        self.db_type = 'auxiliary data for coverages'
        self.db_hash = db_hash
        self.version = anvio.__auxiliary_data_version__
        self.file_path = file_path
        self.quiet = quiet
        self.run = run
        self.progress = progress
        self.numpy_data_type = 'uint16'

        self.db = db.DB(self.file_path, self.version, new_database=create_new)

        if create_new:
            self.create_tables()

        if not ignore_hash:
            self.check_hash()


    def create_tables(self):
        self.db.set_meta_value('db_type', self.db_type)
        self.db.set_meta_value('contigs_db_hash', self.db_hash)
        self.db.set_meta_value('creation_date', time.time())

        self.db.create_table(t.split_coverages_table_name, t.split_coverages_table_structure, t.split_coverages_table_types)


    def check_hash(self):
        actual_db_hash = self.db.get_meta_value('contigs_db_hash')
        if self.db_hash != actual_db_hash:
            raise AuxiliaryDataError('The hash value inside Auxiliary Database "%s" does not match with Contigs Database hash "%s",\
                                      this files probaby belong to different projects.' % (actual_db_hash, self.db_hash))


    def append(self, split_name, sample_name, coverage_list):
        coverage_list_blob = utils.convert_numpy_array_to_binary_blob(np.array(coverage_list, dtype=self.numpy_data_type))
        self.db.insert(t.split_coverages_table_name, values=(split_name, sample_name, coverage_list_blob, ))


    def get_all_known_split_names(self):
        return set(self.db.get_single_column_from_table(t.split_coverages_table_name, 'split_name'))


    def get_all(self):
        return self.get_coverage_for_multiple_splits(self.get_all_known_split_names())


    def get_coverage_for_multiple_splits(self, split_names):
        self.progress.new('Recovering split coverages')
        self.progress.update('...')

        split_coverages = {}
        all_known_splits = self.get_all_known_split_names()

        for split_name in split_names:
            self.progress.update('Processing split "%s"' % split_name)

            split_coverages[split_name] = self.get(split_name)

        self.progress.end()
        return split_coverages        


    def get(self, split_name):
        cursor = self.db._exec('''SELECT sample_name, coverages FROM %s WHERE split_name = "%s"''' % 
                                                 (t.split_coverages_table_name, split_name))

        rows = cursor.fetchall()

        if len(rows) == 0:
            raise AuxiliaryDataError('Database does not know anything about split "%s"' % split_name)

        split_coverage = {}
        for row in rows:
            sample_name, coverage_blob = row # unpack sqlite row tuple

            split_coverage[sample_name] = utils.convert_binary_blob_to_numpy_array(coverage_blob, dtype=self.numpy_data_type).tolist()
        
        return split_coverage


    def close(self):
        self.db.disconnect()


class AuxiliaryDataForNtPositions(object):
    def __init__(self, file_path, db_hash, create_new=False, ignore_hash=False, progress=progress, run=run):
        self.file_path = file_path
        self.db_type = 'auxiliary data for nt positions'
        self.version = anvio.__auxiliary_data_version__
        self.db_hash = db_hash
        self.numpy_data_type = 'uint8'

        self.db = db.DB(self.file_path, self.version, new_database=create_new)

        if create_new:
            self.create_tables()

        if not ignore_hash:
            self.check_hash()


    def create_tables(self):
        self.db.set_meta_value('db_type', self.db_type)
        self.db.set_meta_value('contigs_db_hash', self.db_hash)
        self.db.set_meta_value('creation_date', time.time())

        self.db.create_table(t.nt_position_info_table_name, t.nt_position_info_table_structure, t.nt_position_info_table_types)


    def check_hash(self):
        actual_db_hash = self.db.get_meta_value('contigs_db_hash')
        if self.db_hash != actual_db_hash:
            raise AuxiliaryDataError('The hash value inside Auxiliary Database "%s" does not match with Contigs Database hash "%s",\
                                      this files probaby belong to different projects.' % (actual_db_hash, self.db_hash))


    def is_known_contig(self, contig_name):
        return contig_name in self.db.get_single_column_from_table(t.nt_position_info_table_name, 'contig_name')


    def append(self, contig_name, position_info_list):
        position_info_blob = utils.convert_numpy_array_to_binary_blob(np.array(position_info_list, dtype=self.numpy_data_type))
        self.db.insert(t.nt_position_info_table_name, values=(contig_name, position_info_blob, ))


    def get(self, contig_name):
        if not self.is_known_contig(contig_name):
            return []

        cursor = self.db._exec('''SELECT position_info FROM %s WHERE contig_name = "%s"''' % 
                                                      (t.nt_position_info_table_name, contig_name))

        position_info_blob = cursor.fetchone()[0]
        return utils.convert_binary_blob_to_numpy_array(position_info_blob, dtype=self.numpy_data_type).tolist()


    def close(self):
        self.db.disconnect()
