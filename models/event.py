# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug


from logging import getLogger


_logger = getLogger(__name__)


@api.model
def _lang_get(self):
    languages = self.env['res.lang'].search([])
    return [(language.code, language.name) for language in languages]

class event_organizer(models.Model):
    _name = "event.organizer"
    _description = 'Event Organizer'

    name = fields.Char(
        string='Divison Name',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )

class partner_bu(models.Model):
    _name = "partner.bu"
    _description = 'Business Unit'

    name = fields.Char(
        string='BU Name',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )

@api.model
def _organizer_get(self):
    partners = self.env['event.organizer'].search([])
    return [(partner.id, partner.name) for partner in partners]

# class event_type(models.Model):
#     _inherit = "event.type"

#     level = fields.Selection(
#         string='Event Level',
#         required=True,
#         readonly=False,
#         index=False,
#         help=False,
#         selection=[
#             ('abbvie', 'Abbvie'),
#             ('other', '3rd Partner'),
#             ],
#         default='abbvie',
#         )

#     @api.multi
#     @api.depends('name', 'level')
#     def name_get(self):
#         result = []
#         for etype in self:
#             result.append((etype.id, '%s (%s)' % (etype.name, etype.level)))
#         return result


class event_event(models.Model):
    _inherit = "event.event"

    level = fields.Selection(
        string='Event Level',
        required=True,
        readonly=False,
        index=False,
        help=False,
        selection=[
            ('hospital', 'Hospital'),
            ('city', 'City'),
            ('regional', 'Regional'),
            ('national', 'National'),
            ('international', 'International'), ],
        default='hospital',
    )

    event_code = fields.Char(
        string='Event ID',
        required=True,
        readonly=False,
        index=False,
        help=False,
        size=50,
        states={'done': [('readonly', True)], 'confirm': [('readonly', True)]}
    )

    name = fields.Char(string='Subject', translate=False)

    event_purpose = fields.Selection(
        string='Event Purpose',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=False,
        selection=[('marketing', 'Promotional'), ('communication', 'Disease Awareness')]
    )

    organizer = fields.Selection(_organizer_get, string='Sponsored By',)

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

    @api.model
    def _default_tickets(self):
        try:
            products = self.env['product.product'].search([('event_ok', '=', True)])
            return [{
                'product_id': product.id,
                'price': 0,
            } for product in products]
        except ValueError:
            return self.env['event.event.ticket']

    @api.multi
    @api.depends('name', 'event_code')
    def name_get(self):
        result = []
        for event in self:
            name = super(event_event, self).name_get()[0][1]
            result.append((event.id, '[%s] %s ' % (event.event_code, name)))
        return result

    _defaults = {
        'show_menu': True,
        'show_tracks': True,
        'show_track_proposal': False,
        'date_tz': 'Asia/Shanghai',
    }


class event_ticket(models.Model):
    _inherit = 'event.event.ticket'
    _description = 'Seat Quota'

    user_id = fields.Many2one(
        'res.users', string='Responsible',
        default=lambda self: self.env.user
    )

    product_id = fields.Many2one(string="Attendee Region")
    deadline = fields.Date(string="Nomination End")

    @api.multi
    @api.depends('product_id')
    def name_get(self):
        result = []
        for ticket in self:
            result.append((ticket.id, '%s' % (ticket.product_id.name)))
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

class event_hospital_department(models.Model):
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


class event_service_type(models.Model):
    _name = "event.service.type"
    _description = 'Service Type'

    name = fields.Char(
        string='Type Name',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )

@api.model
def _service_type_get(self):
    svc_types = self.env['event.service.type'].search([])
    return [(svc_type.id, svc_type.name) for svc_type in svc_types]

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

    service_type = fields.Selection(
        _service_type_get,
        string='Service Type',
        required=False,
        readonly=False,
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

    user_id = fields.Many2one(
        'res.users', string='Nominator',
        default=lambda self: self.env.user
    )

    oversea = fields.Boolean(
        string='Oversea',
        required=False,
        readonly=False,
        index=False,
        default=False,
    )

    state = fields.Selection([
        ('draft', 'Proposal'), ('confirmed', 'Confirmed'), ('refused', 'Refused'), ('cancel', 'Cancelled')],
        'Status', default='draft', required=True, copy=False, track_visibility='onchange')

    date = fields.Datetime('Topic Date')

    nbr_hour = fields.Integer(
        string='Duration',
        required=False,
        readonly=False,
        index=False,
        default=1,
        help=False
    )

    nbr_minute = fields.Selection(
        [('0', '00'), ('15', '15'), ('30', '30'), ('45', '45')],
        string='Minutes',
        required=False,
        readonly=False,
        index=False,
        help=False,
        default='0'
    )

    @api.multi
    @api.depends('nbr_hour', 'nbr_minute')
    def _compute_duration(self):
        if self.nbr_hour and self.nbr_minute:
            self.duration = float(self.nbr_hour) + float(self.nbr_minute) / 60
        else:
            self.duration = 0.0

    duration = fields.Float('Hours', digits=(2, 2), compute='_compute_duration')

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

    registration_id = fields.Many2one(
        string='Attendee',
        required=True,
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

    identifier_id = fields.Char(
        string='Identifier ID')

    bank_account = fields.Char(
        string='Bank Account')

    partner_name = fields.Char('Name')
    partner_email = fields.Char('Email')
    partner_phone = fields.Char('Phone')

    # @api.onchange('registration_id')
    # def _onchange_registration_id(self):
    #     if self.registration_id:
    #         contact= self.registration_id.partner_id
    #         if contact:
    #             self.speaker_id = self.registration_id.partner_id

    @api.onchange('speaker_id')
    def _onchange_partner(self):
        if self.speaker_id:
            contact_id = self.speaker_id.address_get().get('contact', False)
            if contact_id:
                contact = self.env['res.partner'].browse(contact_id)
                self.partner_name = contact.name
                self.partner_email = contact.email
                self.partner_phone = contact.phone
                self.oversea = contact.oversea

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
        [('single', 'Single'), ('standard', 'Standard')],
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
    )

    travel_destionation = fields.Char(
        string='Destination',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
    )

    freight = fields.Char(
        string='Flight/Trian No.',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        oldname='fleight_ticket_no'
    )


class event_registration(models.Model):
    _inherit = "event.registration"

    _description = 'Nomination'

    user_id = fields.Many2one(
        'res.users', string='Nominator',
        default=lambda self: self.env.user,
        readonly=False, states={'done': [('readonly', True)]})

    event_ticket_id = fields.Many2one(required=True, string="Region")
    partner_id = fields.Many2one(required=True)
    venue = fields.Char(
        string='Venue',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        related='event_id.venue',
    )

    hotel_budget = fields.Float(
        string='Hotel Budget',
        required=False,
        readonly=False,
        index=False,
        default=1500.0,
        digits=(4, 2),
        help=False
    )

    travel_budget = fields.Float(
        string='Travel Budget',
        required=False,
        readonly=False,
        index=False,
        default=2000.0,
        digits=(4, 2),
        help=False
    )

    sponsorship_amount = fields.Float(
        string='Sponsorship Amount',
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(4, 2),
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

    # @api.multi
    # @api.depends('name', 'event_id')
    # def name_get(self):
    #     result = []
    #     for attendee in self:
    #         result.append((attendee.id, '%s (%s)' % (attendee.name, attendee.event_id.name)))
    #     return result




    @api.onchange('partner_id')
    def _onchange_partner(self):
        if self.partner_id:
            contact_id = self.partner_id.address_get().get('contact', False)
            if contact_id:
                contact = self.env['res.partner'].browse(contact_id)
                self.name = contact.name
                self.email = contact.email
                self.phone = contact.phone

                team = contact.team_id

                dom = ""
                if contact.speaker and team:
                    dom = "%s-%s" % (team.name, 'Speaker')
                elif contact.employee:
                    dom = "Internal-Audience"
                elif not contact.employee and not contact.speaker and team:
                    dom = "%s-%s" % (team, 'Audience')

                _logger.info('domain is %s ' %dom)

                product_ticket = self.env['product.product'].search([('name', '=', dom)])
                _logger.info('product ticket is  %s ' %product_ticket)

                if product_ticket:
                    ticket_ids = self.env['event.event.ticket'].search([('product_id', 'in', [product_ticket.id]), ('event_id', '=', self.env.context.get('event_id'))])
                    _logger.info('ticket ids is  %s ' %ticket_ids)
                    if ticket_ids:
                        self.event_ticket_id = ticket_ids[0]
