# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug


@api.model
def _lang_get(self):
    languages = self.env['res.lang'].search([])
    return [(language.code, language.name) for language in languages]

@api.model
def _organizer_get(self):
    partners = self.env['res.partner'].search([('organizer', '=', True)])
    return [(partner.id, partner.name) for partner in partners]

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
            ('international_other', 'International [3rd Partner]'), ],
        default='hospital',
        )

    @api.multi
    @api.depends('name', 'level')
    def name_get(self):
        result = []
        for etype in self:
            result.append((etype.id, '%s (%s)' % (etype.name, etype.level)))
        return result


class event_event(models.Model):
    _inherit = "event.event"

    event_code = fields.Char(
        string='Event ID',
        required=True,
        readonly=False,
        index=False,
        help=False,
        size=50,
        states={'done': [('readonly', True)], 'confirm': [('readonly', True)]}
    )

    name = fields.Char(translate=False)

    organizer_id = fields.Selection(_organizer_get, string='Organizer',)

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

    main_brand = fields.Many2one(
        string='Main Brand',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.brand',
        domain=[],
        context={},
        limit=None
    )

    brands = fields.Many2many(
        string='Supported Brands',
        required=False,
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

    lang = fields.Selection(_lang_get,
        string='Language',
        required=True,
        default=lambda self: self.env.user.lang
    )

    venue = fields.Char(
        string='Venue',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50
    )

    count_tracks = fields.Integer(string='Topics')

    _defaults = {
        'show_menu': True,
        'show_tracks': True,
        'show_track_proposal': False,
        'date_tz': 'Asia/Shanghai',
        'event_ticket_ids': None,
    }

class event_registration(models.Model):
    _inherit = 'event.registration'
    _description = 'Nomination'

    event_ticket_id = fields.Many2one(required=True, string="Region")
    partner_id = fields.Many2one(required=True)

class event_ticket(models.Model):
    _inherit = 'event.event.ticket'
    _description = 'Nomination'

    product_id = fields.Many2one(string="Region")
    deadline = fields.Date(string="Nomination End")

    @api.multi
    @api.depends('name', 'product_id')
    def name_get(self):
        result = []
        for ticket in self:
            result.append((ticket.id, '%s (%s)' % (ticket.name, ticket.product_id.name)))
        return result

    _defaults = {
        'name': 'Audience',

    }


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
    # brand_type = fields.Selection(
    #     string='Brand Type',
    #     required=False,
    #     readonly=False,
    #     index=False,
    #     default=False,
    #     help=False,
    #     selection=[('main', 'Main'), ('other', 'Other')]
    # )

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

    location_id = fields.Char('Room')

    event_track = fields.Many2one(
        string='Topic',
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

    date = fields.Datetime('Topic Date')

    event_track_contract = fields.One2many(
        string='service contract',
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

    speaker_id = fields.Many2one('res.partner', string='Speaker', required=True, domain="[('speaker', '=', 'True')]")

    identifier_id = fields.Char(
        string='Identifier ID')

    bank_account = fields.Char(
        string='Bank Account')

    partner_name = fields.Char('Name')
    partner_email = fields.Char('Email')
    partner_phone = fields.Char('Phone')

    @api.onchange('speaker_id')
    def _onchange_partner(self):
        if self.speaker_id:
            contact_id = self.speaker_id.address_get().get('contact', False)
            if contact_id:
                contact = self.env['res.partner'].browse(contact_id)
                self.partner_name = self.partner_name or contact.name
                self.partner_email = self.partner_email or contact.email
                self.partner_phone = self.partner_phone or contact.phone

class event_registration_hotel(models.Model):
    _name = "event.registration.hotel"
    _description = 'registration hotel'

    registration = fields.Many2one(
        string='Attendee',
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
        string='Partner',
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

    hotel_address = fields.Char(
        string='Hotel',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.partner',
        domain="[('hotel', '=', 'True')]",
        context={},
        ondelete='cascade',
        auto_join=False
    )

    hotel_room = fields.Selection(
        [('single', 'Signle Bed'), (('double', 'Double Bed'))],
        string='Room Type',
        required=False,
        readonly=False,
        index=False,
        default='single',
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

    _description = 'registration travel'

    registration = fields.Many2one(
        string='Attendee',
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
        string='Partner',
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

    freight = fields.Char(
        string='Flight/Trian',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True,
        oldname='fleight_ticket_no'
    )


class event_registration(models.Model):
    _inherit = "event.registration"

    hotel_budget = fields.Float(
        string='Hotel Budget',
        required=False,
        readonly=False,
        index=False,
        default=1500.0,
        digits=(16, 2),
        help=False
    )

    travel_budget = fields.Float(
        string='Travel Budget',
        required=False,
        readonly=False,
        index=False,
        default=2000.0,
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
