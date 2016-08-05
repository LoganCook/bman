import logging

from usage.models import University, UniversityD, UniversityDD

logger = logging.getLogger(__name__)


class Importer(object):
    CLASSIFIER_KEYS = ['one', 'two', 'three']

    def __init__(self, start_ts, end_ts, data, manager, fields, unique_field):
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.usages = data
        self.manager = manager
        self.FIELDS = fields
        self.unique_field = unique_field

    def _insert(self, usage):
        """Insert usage of an usage"""

        # usage['manager'] holds manager's organisations at the most three levels
        # They have to be mapped to University, UniversityD and UniversityDD
        # initialise model_data with classifiers
        model_data = self._get_classifiers(usage['manager'])
        if len(model_data) == 0:
            logger.warning('Skipped: usage identified by id=%s has no manager data.' % usage[self.unique_field])
            return False

        if self._exists(usage):
            logger.debug('Skipped: usage identified by id=%s is in database.' % usage[self.unique_field])
            return False

        for f in self.FIELDS:
            model_data[f] = usage[f]
        model_data['start_ts'] = self.start_ts
        model_data['end_ts'] = self.end_ts

        self.manager.create(**model_data)
        return True

    def _exists(self, usage):
        """Check if an usage of an instance has alreay ingested"""
        filters = {
            'start_ts': self.start_ts,
            'end_ts': self.end_ts,
            self.unique_field: usage[self.unique_field]
        }
        rslt = self.manager.filter(**filters)
        return len(rslt) > 0

    def insert(self):
        count = 0
        for usage in self.usages:
            if self._insert(usage):
                count += 1
        logger.info('Ingest %d out of %d' % (count, len(self.usages)))

    def _get_classifier_id(self, lvl, name, parent_id=None):
        """Get or create an University[,D,DD] instance id"""
        assert lvl in [0, 1, 2], 'Wrong classification level provied: has to be one of 0, 1, 2'
        # lvl is 0 based
        if lvl == 0:
            classifier, _ = University.objects.get_or_create(name=name)
        elif lvl == 1:
            classifier, _ = UniversityD.objects.get_or_create(name=name, parent_id=parent_id)
        elif lvl == 2:
            classifier, _ = UniversityDD.objects.get_or_create(name=name, parent_id=parent_id)
        return classifier.id

    def _get_classifiers(self, names):
        classifier_ids = []
        key_names = []
        for lvl in range(len(names)):
            if lvl > 0:
                classifier_ids.append(self._get_classifier_id(lvl, names[lvl], parent_id=classifier_ids[lvl - 1]))
            else:
                classifier_ids.append(self._get_classifier_id(lvl, names[lvl]))
            key_names.append('class_%s_id' % self.CLASSIFIER_KEYS[lvl])
        return dict(zip(key_names, classifier_ids))
