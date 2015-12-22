# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

import logging
_logger = logging.getLogger(__name__)


class CountryStateCity(models.Model):
    _name = 'res.country.state.city'
    _description = 'City'

    state_id = fields.Many2one(
        string='State',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.country.state',
        domain=[],
        context={},
        auto_join=False
    )

    name = fields.Char(
        string='City Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=50,
        translate=True
    )

    code = fields.Char(string= 'City Code', size=5, required=True)


@api.model
def _partner_bu_get(self):
    bus = self.env['partner.bu'].search([])
    return [(bu.name, bu.name) for bu in bus]


class Partner(models.Model):
    _inherit = "res.partner"

    code = fields.Char(
        string='Code',
    )

    team_id = fields.Many2one(
        string='Region',
    )

    user_id = fields.Many2one(
        'res.users', string='Responsible',
        default=lambda self: self.env.user,
    )

    unit = fields.Selection(
        _partner_bu_get,
        string='Business Unit',
        required=False,
        readonly=False,
    )

    department = fields.Many2one(
        string='Department',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='event.department',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    gender = fields.Selection(
         string='Gender',
         required=False,
         readonly=False,
         index=False,
         help=False,
         selection=[('male', 'Male'), ('female', 'Female')]
        )

    speaker = fields.Boolean(
        string='Is a Speaker',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=False
    )

    hotel = fields.Boolean(
        string='Is a Hotel',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=False
    )

    oversea = fields.Boolean(
        string='Oversea',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=False
    )

    employee = fields.Boolean(
        string='Is a Employee',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=False
    )

    report_to = fields.Many2one(
        string='1st Line Manager',
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

    property_account_receivable_id = fields.Many2one(required=False)
    property_account_payable_id = fields.Many2one(required=False)

    @api.multi
    @api.depends('name', 'code')
    def name_get(self):
        result = []
        name_list = super(Partner, self).name_get()

        for name in name_list:
            partner_id = name[0]
            partner = self.env['res.partner'].browse(partner_id)
            if partner.code:
                result.append((partner.id, '[%s] %s ' % (partner.code, partner.name)))
            else:
                result.append((partner.id, partner.name))
        return result

    city = fields.Many2one(
        string='City',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='res.country.state.city',
        domain=[],
        context={},
        auto_join=False
    )

    @api.onchange('city')
    def onchange_city(self):
        if self.city:
            self.state_id = self.city.state_id

from openerp.osv import osv, fields

class res_partner(osv.Model):
    _inherit = "res.partner"

    _columns = {
        'type': fields.selection(
            [('other', 'Address'),
             ('contact', 'Contact'),
             ('invoice', 'Invoice address'),
             ('delivery', 'Shipping address'),
             ], 'Address Type',
                )
    }

    _defaults = {

        'type': 'other',

    }
