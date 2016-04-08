// License, author and contributors information in:
// __openerp__.py file at the root folder of this module.

openerp.base_import_csv_optional = function (instance) {
    var QWeb = instance.web.qweb;
    var _t = instance.web._t;
    var _lt = instance.web._lt;

    instance.web.ListView.prototype.defaults.import_enabled = false;
    base_import_csv_optional = instance.web.ListView.include({
        render_buttons: function () {

        var self = this;
        var import_enabled = false;
        var Users = new openerp.web.Model('res.users');
        this._super.apply(this, arguments); // Sets this.$buttons

        Users.call('has_group', ['base_import_csv_optional.group_import_csv']).then(function(result){
            import_enabled = result;

        if(!import_enabled) { // Remove import button if it's not enabled for the users, Otherwise the parents will render buttons.
//Gavin: 20160116, use current instance view to find button and remove
            self.buttons = instance.web.ListView.buttons;
            self.$buttons.find('.o_list_button_import').remove();

            return false;

        }

        });


        return this.$buttons;
    }
    });
};
