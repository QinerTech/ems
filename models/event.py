# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug


class event_type(models.Model):
    _inherit = "event.type"

    level = fields.Selection(
        string='Event Level',
        required=True,
        readonly=False,
        index=False,
        help=False,
        selection=[
            ('national', 'National'),
            ('regional', 'Regional'),
            ('city', 'City'),
            ('hospital', 'Hospital'),
            ('medical_society_national', 'Mediacal Society National [3rd Partner]'),
            ('medical_society_regional', 'Mediacal Society Regional [3rd Partner]'),
            ('medical_society_city', 'Mediacal Society City [3rd Partner]'),
            ('international', 'International'),
            ('international_other', 'International [3rd Partner]'), ]
        )


class event_event(models.Model):
    _inherit = "event.event"

    event_code = fields.Char(
        string='Event ID',
        required=True,
        readonly=False,
        index=False,
        help=False,
        size=50,
        states={'done': [('readonly', True)], 'confirm': [('readonly', True) ]}
    )

    hotel = fields.One2many(
        string='Hotel',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.registration.hotel',
        inverse_name='event',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    travel = fields.One2many(
        string='Travel',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.registration.travel',
        inverse_name='event',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    contract = fields.One2many(
        string='Contract',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.track.contract',
        inverse_name='event',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    brands = fields.Many2many(
        string='Supported Brands',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.brand',
        relation='event_brand_event_rel',
        column1='brand_id',
        column2='event_id',
        domain=[],
        context={},
        limit=None
    )

    departments = fields.Many2many(
        string='Related Departments',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.department',
        relation='event_department_event_rel',
        column1='department_id',
        column2='event_id',
        domain=[],
        context={},
        limit=None
    )

    lang = fields.Many2one(
        string='Language',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.lang',
        domain=[],
        context={},
        ondelete='cascade',
        states={'done': [('readonly', True)], 'confirm': [('readonly', True) ]}
    )

    venue = fields.Char(
        string='Venue',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        states={'done': [('readonly', True)], 'confirm': [('readonly', True) ]}
    )

    count_tracks = fields.Integer(string='Topics')

    _defaults = {
        'show_menu': True,
        'show_tracks': True,
        'show_track_proposal': False,
        'date_tz': 'Asia/Shanghai',
    }

class event_registration(models.Model):
    _inherit = 'event.registration'

    event_ticket_id = fields.Many2one(required=True)
    partner_id = fields.Many2one(required=True)

class event_brand(models.Model):
    _name = "event.brand"

    name = fields.Char(
        string='Brand Name',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )
    # event_id = fields.Many2one('event.event', 'Event', required=True)
    image_medium = fields.Binary(string='Logo', store=True, attachment=True)
    brand_type = fields.Selection(
        string='Brand Type',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=False,
        selection=[('main', 'Main'), ('other', 'Other')]
    )

class event_department(models.Model):
    _name = "event.department"
    _description = 'Event Department'

    name = fields.Char(
        string='Name',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )


class event_track_contract(models.Model):
    _name = "event.track.contract"
    _description = 'Event Track Contract'

    event_track = fields.Many2one(
        string='Track',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.track',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    event = fields.Many2one(
        string='Event',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.event',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        related='event_track.event_id',
        store=True
    )

    speaker = fields.Many2one(
        string='Speaker',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.partner',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        related='event_track.speaker_id',
        store=True
    )

    service_type = fields.Char(
        string='Service Type',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )

    service_fee = fields.Float(
        string='Service Fee',
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    serivce_deliverable = fields.Char(
        string='Serivce Deliverable',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )

    resonable_requirement = fields.Char(
        string='Resonable Requirement',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )


class event_track(models.Model):
    _inherit = "event.track"

    event_track_contract = fields.One2many(
        string='contract for Event track',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.track.contract',
        inverse_name='event_track',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    speaker_id = fields.Many2one('res.partner', string='Speaker', required=True,)


class event_registration_hotel(models.Model):
    _name = "event.registration.hotel"
    _description = 'Event registration sponsorship hotel'

    registration = fields.Many2one(
        string='Registration',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.registration',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    event = fields.Many2one(
        string='Event',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.event',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        related='registration.event_id',
        store=True
    )

    partner = fields.Many2one(
        string='Audience',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.partner',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        related='registration.partner_id',
        store=True
    )

    hotel_address = fields.Many2one(
        string='Hotel',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.partner',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    hotel_room = fields.Char(
        string='Room',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )

    hotel_reservation_start_date = fields.Date(
        string='Start Date',
        required=False,
        readonly=False,
        index=False,
        default=fields.Date.today(),
        help=False
    )

    reversed_days = fields.Integer(
        string='Reserved Days',
        required=False,
        readonly=False,
        index=False,
        default=1,
        help=False
    )


class event_registration_travel(models.Model):
    _name = "event.registration.travel"

    _description = 'Event registration travel'

    registration = fields.Many2one(
        string='Registration',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.registration',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    event = fields.Many2one(
        string='Event',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.event',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        related='registration.event_id',
        store=True
    )

    partner = fields.Many2one(
        string='Audience',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.partner',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        related='registration.partner_id',
        store=True
    )

    travel_method = fields.Selection(
        string='Travel Method',
        required=False,
        readonly=False,
        index=False,
        default='air',
        help=False,
        selection=[('air', 'Air'), ('train', 'Train'), ('bus', 'Bus'), ('drive', 'Drive')]
    )

    travel_departure_date = fields.Datetime(
        string='Departure Date',
        required=False,
        readonly=False,
        index=False,
        default=fields.Date.today(),
        help=False
    )

    travel_departure = fields.Char(
        string='Departure',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )

    travel_destionation = fields.Char(
        string='Destionation',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )

    fleight_ticket_no = fields.Char(
        string='Ticket No',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )


class event_registration(models.Model):
    _inherit = "event.registration"

    hotel_budget = fields.Float(
        string='Hotel Budget',
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    travel_budget = fields.Float(
        string='Travel Budget',
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(16, 2),
        help=False
    )

    hotel = fields.One2many(
         string='Hotel',
         required=False,
         readonly=False,
         index=False,
         default=None,
         help=False,
         comodel_name='event.registration.hotel',
         inverse_name='registration',
         domain=[],
         context={},
         auto_join=False,
         limit=None
        )

    travel = fields.One2many(
        string='Travel',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.registration.travel',
        inverse_name='registration',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )
