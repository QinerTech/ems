# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

from openerp.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_TIME_FORMAT
from datetime import datetime, timedelta
from openerp.exceptions import UserError, Warning 

from logging import getLogger
import base64
import xlwt
from StringIO import StringIO

_logger = getLogger(__name__)

class product_template(models.Model):
    _inherit = "product.template"

    name = fields.Char(
        translate=False
    )

@api.model
def _lang_get(self):
    languages = self.env['res.lang'].search([])
    return [(language.code, language.name) for language in languages]

class event_type(models.Model):
    _inherit = "event.type"

    level = fields.Selection(
        string='Event Level',
        required=True,
        readonly=False,
        index=False,
        help=False,
        selection=[
            ('abbvie', 'Abbvie'),
            ('other', '3rd Partner'),
            ],
        default='abbvie',
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
        'partner.organization.unit', string='Organizer', required=True,
        default=lambda self: self.env.user.partner_id.organization_unit)

    address_id = fields.Many2one('res.country.state.city', string='City', default=False, required=True)
    country_id = fields.Many2one('res.country', 'Country', related='address_id.state_id.country_id', store=True)

    deadline = fields.Date("Nomination End")

    topic_ids = fields.One2many(
        string='Topics',
        required=False,
        readonly=False,
        index=False,
        default=None,
        comodel_name='event.topic',
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
        compute='_count_contract'
    )

    @api.multi
    def _count_contract(self):
        for event in self:
            event.contract_count = len(self.env['event.topic'].search([('event', '=', self.id)]))

    @api.multi
    def export_travel_info(self):

        data = base64.encodestring(self.from_data(self.registration_ids))
        attach_vals = {
             'name': 'travel_list.xls',
             'datas': data,
             'datas_fname': 'travel_list.xls',
             'res_id': self.id
         }

        existed = self.env['ir.attachment'].search([('name','=','travel_list.xls')])
        if existed:
           existed.unlink()

        doc = self.env['ir.attachment'].create(attach_vals)

        web_url = self.env['ir.config_parameter'].get_param('web.base.url')
        content_url = '/web/content/%s/%s' % (doc.id, 'travel_list.xls')
        url = web_url + content_url

        _logger.info('doc %s, doc_id is %s, url is %s'  % (doc, doc.id, url))

        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'self',
            }

    @api.model
    def from_data(self, vals):
        workbook = xlwt.Workbook(encoding='utf-8')

        header_title = xlwt.easyxf("font: bold on,height 400; pattern: pattern solid, fore_colour white;align:horizontal center, indent 1,vertical center")

        content_title = xlwt.easyxf("font: bold on;align:horizontal left;borders: left thin, top  thin,bottom thin, right thin")

        content = xlwt.easyxf("align:horizontal left;borders: left thin, top  thin, bottom thin, right thin")

        worksheet = workbook.add_sheet('sheet1')
        if (worksheet):
            #worksheet.insert_bitmap('http://localhost:8069/web/binary/company_logo?db=XLD&amp;company=1', 0, 0)
            worksheet.write_merge(0, 0, 0, 3, u'行程安排', header_title)


            startRow = 5

            worksheet.write(startRow, 1, "#", content_title)
            worksheet.write(startRow, 2, u"区域", content_title)
            worksheet.write(startRow, 3, u"城市", content_title)
            worksheet.write(startRow, 4, u"姓名", content_title)
            worksheet.write(startRow, 5, u"性别", content_title)
            worksheet.write(startRow, 6, u"医院", content_title)
            worksheet.write(startRow, 7, u"职称", content_title)
            worksheet.write(startRow, 8, u"手机", content_title)
            worksheet.write(startRow, 9, u"身份证", content_title)
            worksheet.write(startRow, 10, u"出发城市", content_title)
            worksheet.write(startRow, 11, u"到达城市", content_title)
            worksheet.write(startRow, 12, u"出发日期", content_title)
            worksheet.write(startRow, 13, u"出发方式", content_title)
            worksheet.write(startRow, 14, u"去程推荐航班", content_title)
            worksheet.write(startRow, 15, u"去程航班时间", content_title)
            worksheet.write(startRow, 16, u"出发城市", content_title)
            worksheet.write(startRow, 17, u"返回城市", content_title)
            worksheet.write(startRow, 18, u"返回日期", content_title)
            worksheet.write(startRow, 19, u"返程方式", content_title)
            worksheet.write(startRow, 20, u"返程推荐航班", content_title)
            worksheet.write(startRow, 21, u"返程航班时间", content_title)
            worksheet.write(startRow, 22, u"负责人", content_title)
            worksheet.write(startRow, 23, u"负责人手机", content_title)
            worksheet.write(startRow, 24, u"房间类型", content_title)
            worksheet.write(startRow, 25, u"入住日期", content_title)
            worksheet.write(startRow, 26, u"预定天数", content_title)
            worksheet.write(startRow, 27, u"备注", content_title)

            index = 0
            startRow = 6
            for val in vals:
                worksheet.write(startRow + index, 1, index + 1, content)
                worksheet.write(startRow + index, 2, val.partner_id.team_id.name, content)
                worksheet.write(startRow + index, 3, val.partner_id.city, content)
                worksheet.write(startRow + index, 4, val.partner_id.name, content)
                worksheet.write(startRow + index, 5, val.partner_id.gender, content)
                worksheet.write(startRow + index, 6, val.partner_id.parent_id.name, content)
                worksheet.write(startRow + index, 7, val.partner_id.function.name, content)
                worksheet.write(startRow + index, 8, val.partner_id.mobile, content)
                worksheet.write(startRow + index, 9, val.partner_id.identifier_id, content)
                worksheet.write(startRow + index, 10, val.arrival_departure, content)
                worksheet.write(startRow + index, 11, val.arrival_destionation, content)
                worksheet.write(startRow + index, 12, val.arrival_date, content)
                worksheet.write(startRow + index, 13, val.arrival_method, content)
                worksheet.write(startRow + index, 14, val.arrival_freight, content)
                worksheet.write(startRow + index, 15, val.arrival_freight_timeslot, content)
                worksheet.write(startRow + index, 16, val.return_departure, content)
                worksheet.write(startRow + index, 17, val.return_destionation, content)
                worksheet.write(startRow + index, 18, val.return_date, content)
                worksheet.write(startRow + index, 19, val.return_method, content)
                worksheet.write(startRow + index, 20, val.return_freight, content)
                worksheet.write(startRow + index, 21, val.return_freight_timeslot, content)
                worksheet.write(startRow + index, 22, val.user_id.partner_id.name, content)
                worksheet.write(startRow + index, 23, val.user_id.partner_id.mobile, content)
                worksheet.write(startRow + index, 24, val.hotel_room_type, content)
                worksheet.write(startRow + index, 25, val.hotel_reservation_date, content)
                worksheet.write(startRow + index, 26, val.reversed_days, content)
                worksheet.write(startRow + index, 27, "", content)
                index += 1

        fd = StringIO()
        workbook.save(fd)
        fd.seek(0)
        data=fd.read()
        fd.close()
        return data

    @api.multi
    def clean_privacy_data(self):
        for event in self:
            for topic in event.topic_ids:
                topic.write({'bank_account': 'cleaned', 'identifier_id': 'cleaned'})
            for registration in event.registration_ids:
                registration.write({'bank_account': 'cleaned', 'identifier_id': 'cleaned'})
        return True

    @api.one
    def button_done(self):
        self.clean_privacy_data()
        super(event_event, self).button_done()


class event_ticket(models.Model):
    _inherit = 'event.event.ticket'
    _description = 'Attendee Quota'

    user_id = fields.Many2one(
        'res.users', string='Responsible',
        default=lambda self: self.env.user
    )

    product_id = fields.Many2one(string="Attendee Region")
    deadline = fields.Date(string="Nomination End")
    seats_max  = fields.Integer(
        help="put 0 to ignore this rule "
    )

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

class event_topic(models.Model):
    _name = "event.topic"
    _description = 'Topic'

    name = fields.Char(
        string='Subject',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
    )

    user_id = fields.Many2one('res.users', 'Nominator', track_visibility='onchange', default=lambda self: self.env.user)

    state = fields.Selection([
        ('draft', 'Proposal'), ('confirmed', 'Confirmed'), ('refused', 'Refused'), ('cancel', 'Cancelled')],
        'Status', default='draft', required=True, copy=False, track_visibility='onchange')

    nbr_hour = fields.Integer(
        string='Durations',
        required=True,
        readonly=False,
        index=False,
        default=0,
    )

    nbr_minute = fields.Integer(
        string='Minutes',
        required=True,
        readonly=False,
        index=False,
        default=15
    )

    @api.one
    @api.constrains('nbr_hour', 'nbr_minute')
    def _check_duration_limit(self):
        if self.nbr_hour == 0 and self.nbr_minute < 15: 
            raise Warning(_("The duration can not less than 15 Minutes ! "))
        if self.nbr_minute > 60:
            raise Warning(_("The Minutes can not greater than 60 ! "))

    event = fields.Many2one(
        string='Event',
        required=True,
        readonly=False,
        index=False,
        default=None,
        comodel_name='event.event',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False,
        store=True
    )

    partner_id = fields.Many2one(
        string='Speaker',
        required=True,
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

    partner_name = fields.Char(
        string='Speaker Name',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
    )

    partner_phone = fields.Char(
        string='Speaker Phone',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
    )

    partner_email = fields.Char(
        string='Speaker Email',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
    )

    oversea = fields.Boolean(
        string='Is Oversea',
        related='partner_id.oversea'
    )

    identifier_id = fields.Char(
        string='Identifier ID',
        required=True,
        readonly=False,
        index=False,
        default=None,
        size=20,
    )

    bank_account = fields.Char(
        string='Bank Account',
        required=True,

        )

    service_type = fields.Selection(
        _service_type_get,
        string='Service Type',
        required=False,
        readonly=False,
    )
    service_description = fields.Char(
        string='Service Description',
        required=True,
        readonly=False,
        index=False,
        default=None,
        size=50,
    )

    service_rate = fields.Integer(
        string='Service Rate',
        required=True,
        readonly=False,
        index=False,
        default=None,
        size=20,
    )

    service_rate_type = fields.Selection(
        string='Service Rate Type',
        required=False,
        readonly=False,
        index=False,
        default='event',
        help=False,
        selection=[('hour', 'Hour'), ('event', 'Event')]
    )

    service_deliverable = fields.Char(
        string='Serivce Deliverable',
        required=True,
        readonly=False,
        index=False,
        default=None,
        size=50,
    )

    resonable_requirement = fields.Text(
        string='Resonable Requirement',
        required=True,
        readonly=False,
        index=False,
        default=u"促进中国风湿科学学科的进步与发展",
    )

    @api.multi
    @api.depends('event', 'title')
    def name_get(self):
        result = []
        for contract in self:
            if contract.service_type:
                result.append((contract.id, '%s - %s [ %s ]' % (contract.event.name, contract.name, contract.service_type)))
            else:
                result.append((contract.id, '%s - %s' % (contract.event.name, contract.name)))

	    return result

    @api.model
    def create(self, values):
        _logger.info('values is  %s ' % values)
        _logger.info('create topic ....... ')
        result = super(event_topic, self).create(values)

        registrations = self.env['event.registration'].search([('partner_id', '=', values['partner_id']), ('event_id', '=', values['event'])])
        if not registrations and values['partner_id']:
            _logger.info('create registrations !!!')

            vals = {
                "partner_id": values['partner_id'],
                "event_id": values['event'],
            }

            event_obj = self.env['event.event'].browse(values['event'])
            local_dict = {}

            local_dict['datetime_begin'] = event_obj.date_begin
            local_dict['date_arrive'] = (datetime.strptime(event_obj.date_begin, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=-1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            local_dict['datetime_end'] = datetime.strptime(event_obj.date_end, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
            local_dict['date_leave'] = (datetime.strptime(event_obj.date_end, DEFAULT_SERVER_DATETIME_FORMAT) + timedelta(days=1)).strftime(DEFAULT_SERVER_DATE_FORMAT)
            local_dict['place'] = event_obj.address_id.name
            local_dict['days'] = int((datetime.strptime(local_dict['date_leave'], DEFAULT_SERVER_DATE_FORMAT) - datetime.strptime(local_dict['date_arrive'], DEFAULT_SERVER_DATE_FORMAT)).days)

            contact_id = self.env['res.partner'].browse(values['partner_id']).address_get().get('contact', False)
            if contact_id:
                contact = self.env['res.partner'].browse(contact_id)
                vals['name'] = contact.name
                vals['phone'] = contact.phone
                vals['email'] = contact.email
                vals['oversea'] = contact.oversea
                vals['arrival_date'] = local_dict['date_arrive']
                vals['arrival_departure'] = contact.city
                vals['arrival_destionation'] = local_dict['place']
                vals['return_date'] = local_dict['date_leave']
                vals['return_departure'] = local_dict['place']
                vals['return_destionation'] = contact.city
                vals['hotel_room_type'] = 'standard'
                vals['hotel_reservation_date'] = local_dict['date_arrive']
                vals['reversed_days'] = local_dict['days']

                if contact.speaker:
                    vals['hotel_room_type'] = 'single'

                team = contact.team_id or contact.parent_id.team_id

                dom = "Internal-Audience"
                if contact.speaker and team:
                    dom = "%s-%s" % (team.name, 'Speaker')
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

                self.env['event.registration'].create(vals)

        return result

    @api.multi
    @api.depends('nbr_hour', 'nbr_minute')
    def _compute_duration(self):
        if self.nbr_hour and self.nbr_minute:
            self.duration = float(self.nbr_hour) + float(self.nbr_minute) / 60
        else:
            self.duration = 0.0

    duration = fields.Float('Hours', digits=(2, 2), compute='_compute_duration', store=True)

    @api.multi
    @api.depends('service_rate', 'service_rate_type')
    def _compute_service_fee(self):
        if self.service_rate_type and self.service_rate_type == 'event' :
            self.service_fee = self.service_rate
        elif self.service_rate_type and self.service_rate_type == 'hour' and self.duration :
            self.service_fee = self.service_rate * self.duration
        else:
            self.service_fee = 0.0

    service_fee = fields.Float(
        string='Service Fee',
        required=False,
        digits=(4, 2),
        compute='_compute_service_fee',
        store=True
    )


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        contact = self.partner_id
        if contact:
            self.partner_name = contact.name
            self.partner_email = contact.email
            self.partner_phone = contact.phone
            self.oversea = contact.oversea
            self.identifier_id = contact.identifier_id
            self.bank_account = contact.bank_account


class event_registration(models.Model):
    _inherit = "event.registration"

    _description = 'Nomination'

    user_id = fields.Many2one(
        'res.users', string='Nominator',
        default=lambda self: self.env.user,
        readonly=False, states={'done': [('readonly', True)]})

    partner_id = fields.Many2one(required=True)

    event_ticket_id = fields.Many2one(required=True, string="Region")

    is_speaker = fields.Boolean(
        string='Is a Speaker',
        required=False,
        readonly=False,
        index=False,
        default=False,
        related='partner_id.speaker'
    )

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
                self.oversea = contact.oversea
                self.identifier_id = contact.identifier_id
                self.bank_account = contact.bank_account

                self.arrival_departure = contact.city
                self.return_destionation = contact.city
                self.hotel_room_type = 'standard'

                if contact.speaker:
                    self.hotel_room_type = 'single'

                team = contact.team_id or contact.parent_id.team_id

                dom = "Internal-Audience"
                if contact.speaker and team:
                    dom = "%s-%s" % (team.name, 'Speaker')
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


    _sql_constraints = [
        ('partner_registration_uniq', 'unique (event_id,partner_id)', 'The partner of the event  must be unique !')
    ]

    @api.one
    @api.constrains('event_ticket_id')
    def _check_ticket_out_of_date(self):
        if self.event_ticket_id.is_expired :
            raise UserError(_('Ticket is out of date. '))
