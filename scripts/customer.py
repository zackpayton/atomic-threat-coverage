#!/usr/bin/env python3

from atcutils import ATCutils

from jinja2 import Environment, FileSystemLoader
import os

# ########################################################################### #
# ############################## Customer ################################### #
# ########################################################################### #

ATCconfig = ATCutils.load_config("config.yml")

dr_dirs = ATCconfig.get('detection_rules_directories')

all_rules = []
all_names = []
all_titles = []

for dr_path in dr_dirs:
    rules, paths = ATCutils.load_yamls_with_paths(dr_path)
    all_rules = all_rules + rules
    names = [path.split('/')[-1].replace('.yml', '') for path in paths]
    all_names = all_names + names
    titles = [rule.get('title') for rule in rules]
    all_titles = all_titles + titles

_ = zip(all_rules, all_names, all_titles)
rules_by_title = {title: (rule, name) for (rule, name, title) in _}


class Customer:
    """Class for Customer entity"""

    def __init__(self, yaml_file, apipath=None, auth=None, space=None):
        """ Init method """

        # Init vars
        self.title = None
        self.customer_name = None
        self.description = None
        self.data_needed = None
        self.logging_policies = None
        self.detection_rules = None

        self.yaml_file = yaml_file

        self.apipath, self.auth, self.space = apipath, auth, space

        # The name of the directory containing future markdown Customer
        self.parent_title = "Customers"

        # Init methods
        self.parse_into_fields()

    def parse_into_fields(self):
        """Description"""

        # self.fields contains parsed fields obtained from yaml file
        self.cu_fields = ATCutils.read_yaml_file(self.yaml_file)

        """Fill the fields with values. Put None if key not found"""
        self.title = self.cu_fields.get('title')
        self.customer_name = self.cu_fields.get('customer_name')
        self.description = self.cu_fields.get('description')
        self.data_needed = self.cu_fields.get('dataneeded')
        self.logging_policies = self.cu_fields.get('loggingpolicy')
        self.detection_rules = self.cu_fields.get('detectionrule')

    def get_rules(self):
        """ Retruns list of detection rules for customer
        """
        dr_list_per_customer = [rules_by_title.get(dr_title)[0]
                                for dr_title in self.detection_rules]

        return dr_list_per_customer

    def render_template(self, template_type):
        """Render template with data in it
        template_type:
            - "markdown"
            - "confluence"
        """

        if template_type not in ["markdown", "confluence"]:
            raise Exception(
                "Bad template_type. Available values: " +
                "[\"markdown\", \"confluence\"]")

        # Point to the templates directory
        env = Environment(loader=FileSystemLoader('templates'))

        self.cu_fields.update(
            {'description': self.description.strip()}
        )

        # Transform variables to arrays if not provided correctly in yaml

        if isinstance(self.data_needed, str):
            self.cu_fields.update({'dataneeded': [self.data_needed]})

        if isinstance(self.logging_policies, str):
            self.cu_fields.update({'loggingpolicy': [self.logging_policies]})

        detectionrule_with_path = []

        for title in self.detection_rules:
            if title != 'None':
                name = rules_by_title.get(title)[1]
            else:
                name = ''
            dr = (title, name)
            detectionrule_with_path.append(dr)

        self.cu_fields.update({'detectionrule': detectionrule_with_path})

        # Get proper template
        if template_type == "markdown":
            template = env\
                .get_template('markdown_customer_template.md.j2')

        elif template_type == "confluence":
            template = env.get_template(
                'confluence_customer_template.html.j2')

            self.cu_fields.update(
                {'confluence_viewpage_url':
                    ATCconfig.get('confluence_viewpage_url')})

            if not self.logging_policies:
                self.logging_policies = ["None", ]

            logging_policies_with_id = []

            for lp in self.logging_policies:
                if lp != "None" and self.apipath and self.auth and self.space:
                    logging_policies_id = str(ATCutils.confluence_get_page_id(
                        self.apipath, self.auth, self.space, lp))
                else:
                    logging_policies_id = ""
                lp = (lp, logging_policies_id)
                logging_policies_with_id.append(lp)

            self.cu_fields.update({'loggingpolicy': logging_policies_with_id})

            if not self.data_needed:
                self.data_needed = ["None", ]

            data_needed_with_id = []

            for dn in self.data_needed:
                if dn != "None" and self.apipath and self.auth and self.space:
                    data_needed_id = str(ATCutils.confluence_get_page_id(
                        self.apipath, self.auth, self.space, dn))
                else:
                    data_needed_id = ""
                dn = (dn, data_needed_id)
                data_needed_with_id.append(dn)

            self.cu_fields.update({'data_needed': data_needed_with_id})

            detection_rules_with_id = []

            for dn in self.detection_rules:
                if dn != "None" and self.apipath and self.auth and self.space:
                    detection_rules_id = str(ATCutils.confluence_get_page_id(
                        self.apipath, self.auth, self.space, dn))
                else:
                    detection_rules_id = ""
                dn = (dn, detection_rules_id)
                detection_rules_with_id.append(dn)

            self.cu_fields.update({'detectionrule': detection_rules_with_id})

        self.content = template.render(self.cu_fields)

        return True

    def save_markdown_file(self, atc_dir='../Atomic_Threat_Coverage/'):
        """Write content (md template filled with data) to a file"""

        base = os.path.basename(self.yaml_file)
        title = os.path.splitext(base)[0]

        file_path = atc_dir + self.parent_title + "/" + \
            title + ".md"

        return ATCutils.write_file(file_path, self.content)
