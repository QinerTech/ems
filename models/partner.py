# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug


class Partner(models.Model):
    _inherit = "res.partner"

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

    organizer = fields.Boolean(
        string='Is a Organizer',
        required=False,
        readonly=False,
        index=False,
        default=False,
        help=False
    )


    property_account_receivable_id = fields.Many2one(required=False)
    property_account_payable_id = fields.Many2one(required=False)


class users_view(models.Model):
    _inherit = 'res.users'


