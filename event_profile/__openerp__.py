# -*- coding: utf-8 -*-
{
    'name': "EMS Profile",

    'summary': """
        event management system for abbive""",

    'description': """
        event management system for abbive, this addons install all the required odoo addons for event


    """,

    'author': "jeffery chen fan",
    'website': "http://www.odoouse.cn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['res_roles', 'event', 'event_sale', 'web_m2x_options'],
    'external_dependencies': {'python': ['xlwt']},

    # always loaded
    'data': [
        'data/event_data.xml',
        'data/event.service.type.csv',
        'data/partner.function.csv',
        'data/res.partner.title.csv',
        'data/partner.hospital.unit.csv',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/event_view.xml',
        'views/partner_view.xml',
        'views/event_report.xml',
        'views/report_layout.xml',
        'views/report_event_registration_signin_sheet.xml',
        'views/report_event_speaker_list.xml',
        'views/report_event_registration_travel_list.xml',
        'views/report_event_registration_sponsorship_application.xml',
        'views/report_event_registration_sponsorship_letter.xml',
        'views/report_event_service_contract.xml',
    ],

}
