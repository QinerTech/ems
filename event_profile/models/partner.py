# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

import logging
_logger = logging.getLogger(__name__)


class partner_department(models.Model):
    _name = "partner.organization.unit"
    _description = 'Organization Unit'

    code = fields.Char(
        string='Department Code',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )

    name = fields.Char(
        string='Department Name',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=True
    )

    parent_id = fields.Many2one('partner.organization.unit', string='Parent Organization Unit', select=True, ondelete='cascade')

    child_ids = fields.One2many('partner.organization.unit', 'parent_id', string='Contains')

class partner_hospital_department(models.Model):
    _name = "partner.hospital.unit"
    _description = 'Hospital Unit'

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

class partner_function(models.Model):
    _name = 'partner.function'
    _description = u'Partner Job Position'

    name = fields.Char(
        string='Position Name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help=False,
        size=50,
        translate=True
    )

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

    code = fields.Char(string='City Code', size=5, required=True)


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

    organization_unit = fields.Many2one(
        string='Organization Unit',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='partner.organization.unit',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    hospital_unit = fields.Many2one(
        string='Hospital Unit',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='partner.hospital.unit',
        domain=[],
        context={},
        ondelete='cascade',
        auto_join=False
    )

    function = fields.Many2one(
        string='Job Position',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help=False,
        comodel_name='partner.function',
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

    customer = fields.Boolean(
        string='Is a HCP',
    )

    bank_account = fields.Char(
        string='Bank Account',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=50,
    )

    identifier_id = fields.Char(
        string='Identifier ID',
        required=False,
        readonly=False,
        index=False,
        default=None,
        size=20,
    )

    report_to = fields.Many2one(
        string='Manager',
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

    city = fields.Char(invisible=True)

    city_id = fields.Many2one(
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

    @api.onchange('city_id')
    def _change_city(self):
        if self.city_id:
            self.city = self.city_id.name
            self.state_id = self.city_id.state_id

# from openerp.osv import osv, fields

# class res_partner(osv.Model):
#     _inherit = "res.partner"

#     _columns = {
#         'type': fields.selection(
#             [('other', 'Address'),
#              ('contact', 'Contact'),
#              ('invoice', 'Invoice address'),
#              ('delivery', 'Shipping address'),
#              ], 'Address Type',
#                 )
#     }

#     _defaults = {

#         'type': 'other',
#         'lang': 'zh_CN'

#     }
