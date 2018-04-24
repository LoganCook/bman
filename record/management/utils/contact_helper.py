import json


class ContactHelper(object):
    """Read a JSON file of contacts

    Data is a file saved from the result of Dynamics query for fullname, email, unit and unitAccountID
    unit can be the top Account without parent
    """
    def __init__(self, path):
        # use this url to download and save to json
        # api/data/v8.2/contacts?fetchXml=<fetch mapping%3D"logical">%0A%20%20%20 <entity name%3D"contact">%0A%20%20%20%20%20%20%20 <attribute name%3D"fullname" %2F>%0A%20%20%20%20%20%20%20 <attribute name%3D"emailaddress1" alias%3D"email" %2F>%0A%20%20%20%20%20%20%20 <link-entity name%3D"account" from%3D"accountid" to%3D"parentcustomerid">%0A%20%20%20%20%20%20%20%20%20%20%20 <attribute name%3D"name" alias%3D"unit" %2F>%0A%20%20%20%20%20%20%20%20%20%20%20 <attribute name%3D"accountid" alias%3D"unitAccountID" %2F>%0A%20%20%20%20%20%20%20 <%2Flink-entity>%0A%20%20%20 <%2Fentity>%0A<%2Ffetch>
        # <fetch mapping="logical">
        #     <entity name="contact">
        #         <attribute name="fullname" />
        #         <attribute name="emailaddress1" alias="email" />
        #         <link-entity name="account" from="accountid" to="parentcustomerid">
        #             <attribute name="name" alias="unit" />
        #             <attribute name="accountid" alias="unitAccountID" />
        #         </link-entity>
        #         <filter type='and'>
        #             <condition attribute='emailaddress1' operator='not-null' />
        #         </filter>
        #     </entity>
        # </fetch>
        with open(path, 'r') as jf:
            data = json.load(jf)['value']
        self.indexer = {}
        for entry in data:
            self.indexer[entry['email']] = {
                'name': entry['fullname'],
                'dynamics_id': entry['contactid'],
                'unit': entry['unit'],
                'unit_dynamics_id': entry['unitAccountID']}

    def get(self, email):
        """Find contact infomation by email

        The return structure can be used to create record.Contact instance"""
        return self.indexer[email]
