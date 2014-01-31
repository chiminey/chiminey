import json
import logging

from bdphpcprovider.corestages.stage import Stage
from bdphpcprovider.smartconnectorscheduler.filesystem import DataObject
from bdphpcprovider.smartconnectorscheduler.hrmcstages import get_filesys, get_run_info, get_settings


logger = logging.getLogger(__name__)

# TODO, FIXME: is this package deprecated and can it be removed?

class Schedule(Stage):
    def __init__(self):
        self.settings = {}
        self.group_id = ''

    def triggered(self, context):
        """
            Return True if there is a file system
            but it doesn't contain run_info file.
        """

        if get_filesys(context):
            try:
                get_run_info(context)
            except IOError:
                self.settings = get_settings(context)
                logger.debug("settings = %s" % self.settings)
                return True
        logger.debug("Scheduler not triggered")
        return False

    def process(self, context):
        """ Determine the provider
        """
        questions = [
            ('architecture', "What is the architecture of the computation?", ['Embarrassingly_parallel', 'MapReduce', 'Other']),
            ('size', "How big is the computation", ['small', 'large']),
            ('sensitivity', 'What is the sensitivity of the data of the computation to location?', ['none', 'sensitive'])]

        self.answers = []
        for (quest_num, (question_name, question_desc, question_choices)) in enumerate(questions):
            print "Question %d: %s\n%s\n" % (quest_num + 1, question_name, question_desc)

            valid_input = False
            number_of_fails = 0
            while (not valid_input):
                for (choice_num, choice) in enumerate(question_choices):
                    print "%d %s" % (choice_num + 1, choice)

                input = raw_input("Enter choice: ")
                print input
                mychoice = ""
                try:
                    mychoice = int(input)
                except ValueError as e:
                    print "Invalid input: %s" % e
                    number_of_fails += 1
                else:
                    if mychoice in range(1, len(question_choices) + 1):
                        valid_input = True
                    else:
                        print "Please type number of answer: %s" % mychoice
                        number_of_fails += 1

            self.answers.append(int(mychoice))

        user_requirement = []
        question_no = 0
        for (quest_num, (question_name, question_desc, question_choices)) in enumerate(questions):
            logger.debug("Quest num %d, question name %s " % (quest_num, question_name))
            answer_index = self.answers[quest_num] - 1
            requirement = question_name + '=>' + question_choices[answer_index]
            user_requirement.append(requirement)
            logger.debug("req %s" % requirement)
        logger.debug(user_requirement)

        import DecisionTree

        training_datafile = './smartconnectorscheduler/provider_training.dat'


        #training_datafile = os.path.join(os.path.dirname(__file__),'provider_training.dat').replace('\\','/')


        dt = DecisionTree.DecisionTree(training_datafile=training_datafile,
            entropy_threshold=0.1,
            max_depth_desired=3,
            debug1=1,
            debug2=1
        )
        dt.get_training_data()
        root_node = dt.construct_decision_tree_classifier()
        #   UNCOMMENT THE FOLLOWING LINE if you would like to see the decision
        #   tree displayed in your terminal window:
        #logger.debug(root_node.display_decision_tree("   "))
        classification = dt.classify(root_node, user_requirement)
        max_prob = self._get_highest_probability(classification)
        self.candidate_providers = self._get_candidate_providers(classification, max_prob)
        logger.debug("answers %s" % self.answers)

        return self.answers

    def _get_highest_probability(self, classification):
        which_classes = list(classification.keys())
        max_prob = 0
        for provider in which_classes:
            curr_prob = classification[provider]
            logger.debug("provider %s prob  %f" % (provider, curr_prob))
            if curr_prob > max_prob:
                max_prob = curr_prob
        return max_prob

    def _get_candidate_providers(self, classification, max_prob):
        which_classes = list(classification.keys())
        candidate_providers = []
        for provider in which_classes:
            curr_prob = classification[provider]
            if curr_prob == max_prob:
                candidate_providers.append(provider)
                logger.debug("Candidate provider %s " % provider)
        return candidate_providers

    def output(self, context):
        """
        Create a runfinos.sys file in filesystem with provider
        """
        self.provider = self.candidate_providers[0]
        print "Candidate provider(s) is (are) %s" % self.candidate_providers
        if self.provider != 'nectar' or len(self.candidate_providers) > 1:
            print "But we use 'nectar' for now..."
            self.provider = 'nectar'

        local_filesystem = 'default'
        data_object = DataObject("runinfo.sys")
        data_object.create(json.dumps({'PROVIDER': self.provider}))
        filesystem = get_filesys(context)
        filesystem.create(local_filesystem, data_object)
        return context

