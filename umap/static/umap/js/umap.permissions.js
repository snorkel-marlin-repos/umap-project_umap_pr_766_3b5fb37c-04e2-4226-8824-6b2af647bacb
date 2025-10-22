// Dedicated object so we can deal with a separate dirty status, and thus
// call the endpoint only when needed, saving one call at each save.
L.U.MapPermissions = L.Class.extend({

    options: {
        owner: null,
        editors: [],
        share_status: null,
        edit_status: null
    },

    initialize: function (map) {
        this.setOptions(map.options.permissions);
        this.map = map;
        var isDirty = false,
            self = this;
        try {
            Object.defineProperty(this, 'isDirty', {
                get: function () {
                    return isDirty;
                },
                set: function (status) {
                    isDirty = status;
                    if (status) self.map.isDirty = status;
                }
            });
        }
        catch (e) {
            // Certainly IE8, which has a limited version of defineProperty
        }

    },

    setOptions: function (options) {
        this.options = L.Util.setOptions(this, options);
    },

    isOwner: function () {
        return this.map.options.user && this.options.owner && this.map.options.user.id == this.options.owner.id;
    },

    isAnonymousMap: function () {
        return !this.options.owner;
    },

    getMap: function () {
        return this.map;
    },

    edit: function () {
        if (!this.map.options.umap_id) return this.map.ui.alert({content: L._('Please save the map first'), level: 'info'});
        var container = L.DomUtil.create('div', 'permissions-panel'),
            fields = [],
            title = L.DomUtil.create('h4', '', container);
        if (this.isAnonymousMap()) {
            if (this.options.anonymous_edit_url) {
                var helpText = L._('Secret edit link is:<br>{link}', {link: this.options.anonymous_edit_url});
                fields.push(['options.edit_status', {handler: 'IntSelect', label: L._('Who can edit'), selectOptions: this.map.options.anonymous_edit_statuses, helpText: helpText}]);
            }
        } else {
            if (this.isOwner()) {
                fields.push(['options.edit_status', {handler: 'IntSelect', label: L._('Who can edit'), selectOptions: this.map.options.edit_statuses}]);
                fields.push(['options.share_status', {handler: 'IntSelect', label: L._('Who can view'), selectOptions: this.map.options.share_statuses}]);
                fields.push(['options.owner', {handler: 'ManageOwner', label: L._("Map's owner")}]);
            }
            fields.push(['options.editors', {handler: 'ManageEditors', label: L._("Map's editors")}]);
        }
        title.textContent = L._('Update permissions');
        var builder = new L.U.FormBuilder(this, fields);
        var form = builder.build();
        container.appendChild(form);
        if (this.isAnonymousMap() && this.map.options.user) {
            // We have a user, and this user has come through here, so they can edit the map, so let's allow to own the map.
            // Note: real check is made on the back office anyway.
            var advancedActions = L.DomUtil.createFieldset(container, L._('Advanced actions'));
            var advancedButtons = L.DomUtil.create('div', 'button-bar', advancedActions);
            var download = L.DomUtil.create('a', 'button', advancedButtons);
            download.href = '#';
            download.textContent = L._('Attach the map to my account');
            L.DomEvent
                .on(download, 'click', L.DomEvent.stop)
                .on(download, 'click', this.attach, this);
        }
        this.map.ui.openPanel({data: {html: container}, className: 'dark'});
    },

    attach: function () {
        this.map.post(this.getAttachUrl(), {
            callback: function () {
                this.options.owner = this.map.options.user;
                this.map.ui.alert({content: L._("Map has been attached to your account"), level: 'info'});
                this.map.ui.closePanel();
            },
            context: this
        })
    },

    save: function () {
        if (!this.isDirty) return this.map.continueSaving();
        var formData = new FormData();
        if (!this.isAnonymousMap() && this.options.editors) {
            var editors = this.options.editors.map(function (u) {return u.id});
            for (var i = 0; i < this.options.editors.length; i++) formData.append('editors', this.options.editors[i].id);
        }
        if (this.isOwner() || this.isAnonymousMap()) formData.append('edit_status', this.options.edit_status);
        if (this.isOwner()) {
            formData.append('owner', this.options.owner && this.options.owner.id);
            formData.append('share_status', this.options.share_status);
        }
        this.map.post(this.getUrl(), {
            data: formData,
            context: this,
            callback: function (data) {
                this.isDirty = false;
                this.map.continueSaving();
            }
        });
    },

    getUrl: function () {
        return L.Util.template(this.map.options.urls.map_update_permissions, {'map_id': this.map.options.umap_id});
    },

    getAttachUrl: function () {
        return L.Util.template(this.map.options.urls.map_attach_owner, {'map_id': this.map.options.umap_id});
    },

    addOwnerLink: function (element, container) {
        if (this.options.owner && this.options.owner.name && this.options.owner.url) {
            var ownerContainer = L.DomUtil.add(element, 'umap-map-owner', container, ' ' + L._('by') + ' '),
                owner = L.DomUtil.create('a');
            owner.href = this.options.owner.url;
            owner.textContent = this.options.owner.name;
            ownerContainer.appendChild(owner);
        }
    }

});
