# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_TIME_FORMAT
from datetime import datetime, timedelta

from logging import getLogger


_logger = getLogger(__name__)


@api.model
def _lang_get(self):
    languages = self.env['res.lang'].search([])
    return [(language.code, language.name) for language in languages]

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
        required=False,
        readonly=True,
        index=False,
        size=4,
        states={'done': [('readonly', True)], 'confirm': [('readonly', True)]}
    )

    name = fields.Char(string='Subject', translate=False)

    event_purpose = fields.Selection(
        string='Event Purpose',
        required=False,
        readonly=False,
        index=False,
        default='marketing',
        selection=[('marketing', 'Promotional'), ('communication', 'Disease Awareness'), ('education', 'Patients Education')]
    )

    organization_id = fields.Many2one(
        'partner.organization.unit', string='Organizer',
        default=lambda self: self.env.user.partner_id.organization_unit)

    address_id = fields.Many2one('res.country.state.city', string='City', default=False)
    country_id = fields.Many2one('res.country', 'Country', related='address_id.state_id.country_id', store=True)

    deadline = fields.Date("Nomination End")

    travel = fields.One2many(
        string='Travel',
        required=False,
        readonly=False,
        index=False,
        default=None,
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
        comodel_name='partner.hospital.unit',
        relation='partner_hospital_unit_event_rel',
        column1='hospital_unit_id',
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
        size=50
    )

    @api.onchange('date_begin')
    def _onchange_date_begin(self):
        if self.date_begin:
            self.deadline = (datetime.strptime(self.date_begin, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(-9)).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

    @api.model
    def _default_tickets(self):
        try:
            products = self.env['product.product'].search([('event_ok', '=', True)])
            return [{
                'name': product.name,
                'product_id': product.id,
                'price': 0,
                'deadline': self.deadline,
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

    @api.multi
    def write(self, vals):
        res = super(event_event, self.sudo()).write(vals)
        _vals = {}
        deadline = vals.get('deadline', False)
        if deadline:
            _vals['deadline'] = deadline
            self.env['event.event.ticket'].search([('event_id', '=', self.id)]).write(_vals)

        return res

    _defaults = {
        'event_code': 'New',
        'show_menu': True,
        'show_tracks': True,
        'show_track_proposal': False,
        'date_tz': 'Asia/Shanghai',
        'date_begin': lambda *a: (datetime.now() + timedelta(days=(10))).strftime('%Y-%m-%d 00:00:00'),
        'date_end': lambda *a: (datetime.now() + timedelta(days=(10))).strftime('%Y-%m-%d 09:00:00'),
    }

    @api.model
    def create(self, vals):
        if vals.get('event_code', 'New') == 'New':
            vals['event_code'] = self.env['ir.sequence'].next_by_code('event.event.code') or 'New'

        return super(event_event, self).create(vals)

    @api.one
    def copy(self, default=None):
        default = dict(default or {})
        default['event_code'] = self.env['ir.sequence'].next_by_code('event.event.code') or 'New'

        return super(event_event, self).copy(default)

    contract_count = fields.Integer(
        string='Contract count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        compute = '_count_contract'
    )

    @api.multi
    def _count_contract(self):
        for event in self:
            event.contract_count = len( self.env['event.track.contract'].search( [('event', '=', self.id)]) )

class event_ticket(models.Model):
    _inherit = 'event.event.ticket'
    _description = 'Attendee Quota'

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

    @api.model
    def create(self, vals):
        event_id = vals.get('event_id', False)
        _logger.info('in create method, event_id is %s' % event_id)
        if event_id:
            vals['deadline'] = self.env['event.event'].browse(event_id).deadline

        return super(event_ticket, self).create(vals)

    @api.multi
    def write(self, vals):
        event_id = vals.get('event_id', False)
        _logger.info('in write method, event_id is %s' % event_id)
        if event_id:
            vals['deadline'] = self.env['event.event'].browse(event_id).deadline

        return super(event_ticket, self).write(vals)

class event_brand(models.Model):
    _name = "event.brand"

    name = fields.Char(
        string='Brand Name',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=50,
    )

    image_medium = fields.Binary(string='Logo', store=True, attachment=True)

class event_service_type(models.Model):
    _name = "event.service.type"
    _description = 'Service Type'

    name = fields.Char(
        string='Type Name',
        required=True,
        readonly=False,
        index=False,
        default=None,
        size=50,
    )

@api.model
def _service_type_get(self):
    svc_types = self.env['event.service.type'].search([])
    return [(svc_type.name, svc_type.name) for svc_type in svc_types]

class event_track_contract(models.Model):
    _name = "event.track.contract"
    _description = 'Event Track Contract'

    event_track = fields.Many2one(
        string='Track',
        required=False,
        readonly=False,
        index=False,
        default=None,
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
        comodel_name='res.partner',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        store=True
    )

    oversea = fields.Boolean(
        string='Is Oversea',
        related='speaker.oversea'
    )

    duration = fields.Float('Hours', digits=(2, 2), related='event_track.duration')

    bank_account = fields.Char(
        string='Bank Account')

    identifier_id = fields.Char(
        string='Identifier ID',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=20,
    )


    service_type = fields.Selection(
        _service_type_get,
        string='Service Type',
        required=False,
        readonly=False,
    )
    service_description = fields.Char(
        string='Service Description',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=50,
    )

    service_rate = fields.Float(
        string='Service Rate',
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(4, 2),
    )

    service_fee = fields.Float(
        string='Service Fee',
        required=False,
        readonly=False,
        index=False,
        default=0.0,
        digits=(4, 2),
    )

    service_deliverable = fields.Char(
        string='Serivce Deliverable',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=50,
    )

    resonable_requirement = fields.Text(
        string='Resonable Requirement',
        required=False,
        readonly=False,
        index=False,
        default=u"促进中国风湿科学学科的进步与发展",
    )

    @api.multi
    @api.depends('event','event_track')
    def name_get(self):
        result = []
        for contract in self:
            if contract.service_type:
                result.append((contract.id, '%s - %s [ %s ]' % (contract.event.name, contract.event_track.name, contract.service_type)))
            else:
                result.append((contract.id, '%s - %s' % (contract.event.name, contract.event_track.name)))

        return result

    @api.model
    def create(self, values):
        _logger.info('values is  %s ' % values)

        _logger.info('create contract ....... ')
        result = super(event_track_contract, self).create(values)

        registrations = self.env['event.registration'].search([('partner_id', '=', values['speaker']), ('event_id', '=', values['event'])])
        if not registrations and values['speaker']:
            _logger.info('create registrations !!!')

            vals = {
                "partner_id": values['speaker'],
                "event_id": values['event'],
            }

            event_obj =  self.env['event.event'].browse(values['event'])
            local_dict = {}

            local_dict['datetime_begin'] = event_obj.date_begin
            local_dict['date_arrive'] = (datetime.strptime(event_obj.date_begin, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=-1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            local_dict['datetime_end'] = datetime.strptime(event_obj.date_end, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
            local_dict['date_leave'] = (datetime.strptime(event_obj.date_end, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            local_dict['place'] = event_obj.address_id.name
            local_dict['days'] = int((datetime.strptime(local_dict['date_leave'], DEFAULT_SERVER_DATE_FORMAT) - datetime.strptime(local_dict['date_arrive'], DEFAULT_SERVER_DATE_FORMAT)).days)

            contact_id = self.env['res.partner'].browse(values['speaker']).address_get().get('contact', False)
            if contact_id:
                contact = self.env['res.partner'].browse(contact_id)
                vals['name'] = contact.name
                vals['phone'] = contact.phone
                vals['email'] = contact.email
                vals['oversea'] = contact.oversea

                travel_dict = {}
                travel_dict['arrival_date'] = local_dict['date_arrive']
                travel_dict['arrival_departure'] = contact.city
                travel_dict['arrival_destionation'] = local_dict['place']
                travel_dict['return_date'] = local_dict['date_leave']
                travel_dict['return_departure'] =  local_dict['place']
                travel_dict['return_destionation'] = contact.city
                travel_dict['hotel_room_type'] = 'standard'
                travel_dict['hotel_reservation_date'] = local_dict['date_arrive']
                travel_dict['reversed_days'] = local_dict['days']

                if contact.speaker:
                    travel_dict['hotel_room_type'] = 'single'

                team = contact.team_id or contact.parent_id.team_id

                dom = "Internal-Audience"
                if contact.speaker and team:
                    dom = "%s-%s" % (team.name, 'Speaker')
                elif contact.employee:
                    dom = "Internal-Audience"
                elif not contact.employee and not contact.speaker and team:
                    dom = "%s-%s" % (team.name, 'Audience')

                _logger.info('domain is %s ' % dom)

                product_ticket = self.env['product.product'].search([('name', '=', dom)])
                _logger.info('product ticket is  %s ' % product_ticket)

                if product_ticket:
                    ticket_ids = self.env['event.event.ticket'].search([('product_id', 'in', [product_ticket.id]), ('event_id', '=', values['event'])])
                    _logger.info('ticket ids is  %s ' % ticket_ids)
                    if ticket_ids:
                        vals['event_ticket_id'] = ticket_ids[0].id
                else:
                    vals['event_ticket_id'] = False

                _logger.info('registration values is  %s ' % vals)

                reg =  self.env['event.registration'].create(vals)

                travel_dict['registration'] = reg.id
                _logger.info('travel values is  %s ' % travel_dict)

                travel_obj =  self.env['event.registration.travel'].search([('registration','=',reg.id  )])
                if travel_obj:
                    travel_obj.write(travel_dict)

                else:
                    self.env['event.registration.travel'].create(travel_dict)

        return result

class event_track(models.Model):
    _inherit = "event.track"

    user_id = fields.Many2one(
        'res.users', string='Nominator',
        default=lambda self: self.env.user
    )

    oversea = fields.Boolean(
        string='Is Oversea',
        required=False,
        readonly=False,
        index=False,
        default=False,
    )

    state = fields.Selection([
        ('draft', 'Proposal'), ('confirmed', 'Confirmed'), ('refused', 'Refused'), ('cancel', 'Cancelled')],
        'Status', default='draft', required=True, copy=False, track_visibility='onchange')

    nbr_hour = fields.Integer(
        string='Duration',
        required=False,
        readonly=False,
        index=False,
        default=1,
    )

    nbr_minute = fields.Selection(
        [('0', '00'), ('15', '15'), ('30', '30'), ('45', '45')],
        string='Minutes',
        required=False,
        readonly=False,
        index=False,
        default='0'
    )

    @api.multi
    @api.depends('nbr_hour', 'nbr_minute')
    def _compute_duration(self):
        if self.nbr_hour and self.nbr_minute:
            self.duration = float(self.nbr_hour) + float(self.nbr_minute) / 60
        else:
            self.duration = 0.0

    duration = fields.Float('Hours', digits=(2, 2), compute='_compute_duration', store=True)

    event_track_contract = fields.One2many(
        string='service contract',
        required=False,
        readonly=False,
        index=False,
        # default=lambda self: self._default_contract(),
        comodel_name='event.track.contract',
        inverse_name='event_track',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    @api.model
    def _default_contract(self):

        return [
                {
                    'speaker': False,
                    'service_rate': 3000.00,
                    'service_fee': 3000.00,
                    'service_deliverable': False,
                    'resonable_requirement': u"促进中国风湿科学学科的进步与发展", },
                 {
                    'speaker': False,
                    'service_rate': 3000.00,
                    'service_fee': 3000.00,
                    'service_deliverable': False,
                    'resonable_requirement': u"促进中国风湿科学学科的进步与发展", },
                    {
                    'speaker': False,
                    'service_rate': 3000.00,
                    'service_fee': 3000.00,
                    'service_deliverable': False,
                    'resonable_requirement': u"促进中国风湿科学学科的进步与发展", },
                    {
                    'speaker': False,
                    'service_rate': 3000.00,
                    'service_fee': 3000.00,
                    'service_deliverable': False,
                    'resonable_requirement': u"促进中国风湿科学学科的进步与发展", },
                    {
                    'speaker': False,
                    'service_rate': 3000.00,
                    'service_fee': 3000.00,
                    'service_deliverable': False,
                    'resonable_requirement': u"促进中国风湿科学学科的进步与发展", },
            ]

    @api.onchange('speaker_ids')
    def _onchange_speaker_ids(self):
        contract_list = []

        for speaker in self.speaker_ids:
            contract_data = {
                    'speaker': speaker,
                    'resonable_requirement': u"促进中国风湿科学学科的进步与发展", }

            contract_list += [contract_data]

        self.event_track_contract = contract_list

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        _logger.info('self.event_track_contract is %s ' %(self.event_track_contract))
        contact = self.partner_id
        if contact:
            self.partner_name = contact.name
            self.partner_email = contact.email
            self.partner_phone = contact.phone
            self.oversea = contact.oversea


class event_registration_travel(models.Model):
    _name = "event.registration.travel"

    _description = 'registration travel'

    registration = fields.Many2one(
        string='Attendee',
        required=False,
        readonly=False,
        index=False,
        default=None,
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
        comodel_name='res.partner',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        related='registration.partner_id',
        store=True
    )

    arrival_date = fields.Date(
        string='Arrival Date',
        required=False,
        readonly=False,
        index=False,
        default=fields.Date.today(),
    )

    arrival_departure = fields.Char(
        string='Arrival Departure',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=50,
    )

    arrival_destionation = fields.Char(
        string='Arrival Destination',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=50,
    )

    arrival_method = fields.Selection(
        string='Arrival Method',
        required=False,
        readonly=False,
        index=False,
        default='air',
        selection=[('air', 'Air'), ('train', 'Train'), ('bus', 'Bus'), ('drive', 'Drive')]
    )

    arrival_freight = fields.Char(
        string='Arrival Flight/Trian No.',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=8,
    )

    arrival_freight_timeslot = fields.Char(
        string='Arrival Journey Time',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=8,
    )

    return_date = fields.Date(
        string='Return Date',
        required=False,
        readonly=False,
        index=False,
        default=fields.Date.today(),
    )

    return_departure = fields.Char(
        string='Return Departure',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=50,
    )

    return_destionation = fields.Char(
        string='Return Destination',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=50,
    )

    return_method = fields.Selection(
        string='Return Method',
        required=False,
        readonly=False,
        index=False,
        default='air',
        selection=[('air', 'Air'), ('train', 'Train'), ('bus', 'Bus'), ('drive', 'Drive')]
    )

    return_freight = fields.Char(
        string='Return Flight/Trian No.',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=8,
    )

    return_freight_timeslot = fields.Char(
        string='Return Journey Time',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=8,
    )

    hotel_room_type = fields.Selection(
        [('single', 'Single'), ('standard', 'Standard')],
        string='Room Type',
        required=False,
        readonly=False,
        index=False,
        default='single',
    )

    hotel_reservation_date = fields.Date(
        string='CheckIn Date',
        required=False,
        readonly=False,
        index=False,
        default=fields.Date.today(),
    )

    reversed_days = fields.Integer(
        string='Reserved Days',
        required=False,
        readonly=False,
        index=False,
        default=1,
    )


class event_registration(models.Model):
    _inherit = "event.registration"

    _description = 'Nomination'

    user_id = fields.Many2one(
        'res.users', string='Nominator',
        default=lambda self: self.env.user,
        readonly=False, states={'done': [('readonly', True)]})

    event_ticket_id = fields.Many2one(required=True, string="Region")

    is_speaker = fields.Boolean(
        string='Is a Speaker',
        required=False,
        readonly=False,
        index=False,
        default=False,
        related='partner_id.speaker',
    )

    partner_id = fields.Many2one(required=True)

    oversea = fields.Boolean(
        string='Is Oversea',
        required=False,
        readonly=True,
        index=False,
        default=False,
    )

    identifier_id = fields.Char(
        string='Identifier ID')

    bank_account = fields.Char(
        string='Bank Account')

    venue = fields.Char(
        string='Venue',
        required=False,
        readonly=False,
        index=False,
        default=None,
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
    )

    travel_budget = fields.Float(
        string='Travel Budget',
        required=False,
        readonly=False,
        index=False,
        default=2000.0,
        digits=(4, 2),
    )

    sponsorship_amount = fields.Float(
        string='Sponsorship Amount',
        required=False,
        readonly=False,
        index=False,
        default=3500.0,
        digits=(4, 2),
    )

    travel = fields.One2many(
        string='Travel',
        required=False,
        readonly=False,
        index=False,
        default=lambda rec: rec._default_travel(),
        comodel_name='event.registration.travel',
        inverse_name='registration',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    @api.model
    def _get_event_data(self):
        local_dict = {}
        context = self.env.context
        event_id = context.get('active_id', False)
        _logger.info('enter get_event_data method, event_id is %s' % event_id)
        if event_id:
            event_obj = self.env['event.event'].browse(event_id)
            local_dict['event_id'] = event_id
            local_dict['datetime_begin'] = event_obj.date_begin
            local_dict['date_arrive'] = (datetime.strptime(event_obj.date_begin, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=-1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            local_dict['datetime_end'] = datetime.strptime(event_obj.date_end, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
            local_dict['date_leave'] = (datetime.strptime(event_obj.date_end, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            local_dict['place'] = event_obj.address_id.name
            local_dict['days'] = int((datetime.strptime(local_dict['date_leave'], DEFAULT_SERVER_DATE_FORMAT) - datetime.strptime(local_dict['date_arrive'], DEFAULT_SERVER_DATE_FORMAT)).days)

        return local_dict

    @api.model
    def _default_travel(self):
        _logger.info('enter _default_travel method ')
        return [
                {
                    'arrival_date': self._get_event_data().get('date_arrive', False),
                    'arrival_departure': '',
                    'arrival_destionation': self._get_event_data().get('place', False),
                    'arrival_method': 'air',

                    'return_date': self._get_event_data().get('date_leave', False),
                    'return_departure': self._get_event_data().get('place', False),
                    'return_destionation': '',
                    'return_method': 'air',

                    'hotel_room_type': 'standard',
                    'hotel_reservation_date': self._get_event_data().get('date_arrive', False),
                    'reversed_days': self._get_event_data().get('days', 1),
                    },
                ]

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

                self.travel['arrival_departure'] = contact.city
                self.travel['return_destionation'] = contact.city
                self.travel['hotel_room_type'] = 'standard'

                if contact.speaker:
                    self.travel['hotel_room_type'] = 'single'

                team = contact.team_id or contact.parent_id.team_id

                dom = ""
                if contact.speaker and team:
                    dom = "%s-%s" % (team.name, 'Speaker')
                elif contact.employee:
                    dom = "Internal-Audience"
                elif not contact.employee and not contact.speaker and team:
                    dom = "%s-%s" % (team.name, 'Audience')

                _logger.info('domain is %s ' % dom)

                product_ticket = self.env['product.product'].search([('name', '=', dom)])
                _logger.info('product ticket is  %s ' % product_ticket)

                if product_ticket:
                    ticket_ids = self.env['event.event.ticket'].search([('product_id', 'in', [product_ticket.id]), ('event_id', '=', self.env.context.get('event_id'))])
                    _logger.info('ticket ids is  %s ' % ticket_ids)
                    if ticket_ids:
                        self.event_ticket_id = ticket_ids[0]

                else:
                    self.event_ticket_id = False
