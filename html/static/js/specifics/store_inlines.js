/*global DateTimeShortcuts, SelectFilter*/
/**
 * Django admin inlines
 *
 * Based on jQuery Formset 1.1
 * @author Stanislaus Madueke (stan DOT madueke AT gmail DOT com)
 * @requires jQuery 1.2.6 or later
 *
 * Copyright (c) 2009, Stanislaus Madueke
 * All rights reserved.
 *
 * Spiced up with Code from Zain Memon's GSoC project 2009
 * and modified for Django by Jannis Leidel, Travis Swicegood and Julien Phalip.
 *
 * Licensed under the New BSD License
 * See: http://www.opensource.org/licenses/bsd-license.php
 */
(function($) {
    'use strict';
    $.fn.formset = function(opts) {
        var options = $.extend({}, $.fn.formset.defaults, opts);
        var $this = $(this);
        var $parent = $this.parent();
        var updateElementIndex = function(el, prefix, ndx) {
            var id_regex = new RegExp("(" + prefix + "-(\\d+|__prefix__))");
            var replacement = prefix + "-" + ndx;
            if ($(el).prop("for")) {
                $(el).prop("for", $(el).prop("for").replace(id_regex, replacement));
            }
            if (el.id) {
                el.id = el.id.replace(id_regex, replacement);
            }
            if (el.name) {
                el.name = el.name.replace(id_regex, replacement);
            }
        };
        var enableAutocomplete = function(element, autocompleteSource)
        {
            element.autocomplete(
            {
                width: 300,
                max: 10,
                delay: 100,
                minLength: 3,
                autoFocus: true,
                cacheLength: 1,
                scroll: true,
                highlight: false,
                source: autocompleteSource,
                focus: function( event, ui )
                {
                    return false;
                },
                change: function( event, ui )
                {
                    return false;
                },
                select: function( event, ui )
                {
                    var prefix = element.closest('div.dynamic-product_set')[0].id;
                    var options = $('#id_'+prefix+'-redirect_services_to').children('option');
                    options.each(function(index, item)
                    {
                        var to = $(item).remove();
                        $('#id_'+prefix+'-redirect_services_from').append(to);
                    });
                    $('#id_'+prefix+'-product_stock').val(ui.item.id);
                    $('#id_'+prefix+'-name').val(ui.item.name);
                    $('#id_'+prefix+'-identifier').val(ui.item.identifier);
                    $('#id_'+prefix+'-upc').val(ui.item.upc);
                    $('#id_'+prefix+'-url').val(ui.item.url);
                    $('#id_'+prefix+'-buy_price').val(ui.item.buy_price);
                    $('#id_'+prefix+'-sell_price').val(ui.item.sell_price);
                    $('#id_'+prefix+'-quantity').val(ui.item.quantity);
                    $('#id_'+prefix+'-fba_fee').val(ui.item.fba_fee);
                    $('#id_'+prefix+'-amazon_fee').val(ui.item.amazon_fee);
                    $('#id_'+prefix+'-shipping_cost').val(ui.item.shipping_cost);
                    $('#id_'+prefix+'-product_cost').val(ui.item.product_cost);
                    $('#id_'+prefix+'-profit_per_unit').val(ui.item.profit_per_unit);
                    $('#id_'+prefix+'-total_profit').val(ui.item.total_profit);
                    $('#id_'+prefix+'-roi').val(ui.item.roi);
                    $('#id_'+prefix+'-rank').val(ui.item.rank);
                    $('#id_'+prefix+'-voi_value').val(ui.item.voi_value);
                    $('#id_'+prefix+'-condition').val(ui.item.condition);
                    $('#id_'+prefix+'-notes').val(ui.item.notes);
                    ui.item.redirect_services.forEach(function(item, index)
                    {
                        var from = $('#id_'+prefix+'-redirect_services_from').children('option[value='+item+']').remove();
                        $('#id_'+prefix+'-redirect_services_to').append(from);
                    });
                    return false;
                }
            })
            .autocomplete( 'instance' )._renderItem = function( ul, item )
            {
              return $( '<li>' )
                .append( '<div>' + item.label + '</div>' )
                .appendTo( ul );
            };
        };
        var clearSelection = function(element)
        {
            element.click(function(e)
            {
                    var prefix = element.closest('div.dynamic-product_set')[0].id;
                    var options = $('#id_'+prefix+'-redirect_services_to').children('option');
                    options.each(function(index, item)
                    {
                        var to = $(item).remove();
                        $('#id_'+prefix+'-redirect_services_from').append(to);
                    });
                    $('#id_'+prefix+'-product_stock').val('');
                    $('#id_'+prefix+'-name').val('');
                    $('#id_'+prefix+'-identifier').val('');
                    $('#id_'+prefix+'-url').val('');
                    $('#id_'+prefix+'-buy_price').val('');
                    $('#id_'+prefix+'-sell_price').val('');
                    $('#id_'+prefix+'-quantity').val('');
                    $('#id_'+prefix+'-fba_fee').val('');
                    $('#id_'+prefix+'-amazon_fee').val('');
                    $('#id_'+prefix+'-shipping_cost').val('');
                    $('#id_'+prefix+'-product_cost').val('');
                    $('#id_'+prefix+'-profit_per_unit').val('');
                    $('#id_'+prefix+'-total_profit').val('');
                    $('#id_'+prefix+'-roi').val('');
                    $('#id_'+prefix+'-rank').val('');
                    $('#id_'+prefix+'-voi_value').val('');
                    $('#id_'+prefix+'-condition').val('');
                    $('#id_'+prefix+'-notes').val('');
                    return false;
            });
        };
        var totalForms = $("#id_" + options.prefix + "-TOTAL_FORMS").prop("autocomplete", "off");
        var nextIndex = parseInt(totalForms.val(), 10);
        var maxForms = $("#id_" + options.prefix + "-MAX_NUM_FORMS").prop("autocomplete", "off");
        // only show the add button if we are allowed to add more items,
        // note that max_num = None translates to a blank string.
        var showAddButton = maxForms.val() === '' || (maxForms.val() - totalForms.val()) > 0;
        $this.each(function(i) {
            $(this).not("." + options.emptyCssClass).addClass(options.formCssClass);
        });
        var forms = $("." + options.formCssClass);
        for (var i = 0, formCount = forms.length; i < formCount; i++)
        {
            enableAutocomplete($(forms.get(i)).find('input.enable-autocomplete-name'),
                                '/' + gettext('en') + '/store/product_name/autocomplete/');
            enableAutocomplete($(forms.get(i)).find('input.enable-autocomplete-asin'),
                                '/' + gettext('en') + '/store/product_asin/autocomplete/');
            enableAutocomplete($(forms.get(i)).find('input.enable-autocomplete-upc'),
                                '/' + gettext('en') + '/store/product_upc/autocomplete/');
            clearSelection($(forms.get(i)).find('a.selection-clear'));
            $(forms.get(i)).find("a." + options.deleteCssClass).click(function(e1)
            {
                e1.preventDefault();
                var row = $(this).closest('div.dynamic-product_set');
                // Remove the parent form containing this button:
                row.remove();
                nextIndex -= 1;
                // If a post-delete callback was provided, call it with the deleted form:
                if (options.removed) {
                    options.removed(row);
                }
                $(document).trigger('formset:removed', [row, options.prefix]);
                // Update the TOTAL_FORMS form count.
                var forms = $("." + options.formCssClass);
                $("#id_" + options.prefix + "-TOTAL_FORMS").val(forms.length);
                // Show add button again once we drop below max
                if ((maxForms.val() === '') || (maxForms.val() - forms.length) > 0) {
                    addButton.parent().show();
                }
                // Also, update names and ids for all remaining form controls
                // so they remain in sequence:
                var i, formCount;
                var updateElementCallback = function() {
                    updateElementIndex(this, options.prefix, i);
                };
                for (i = 0, formCount = forms.length; i < formCount; i++) {
                    updateElementIndex($(forms).get(i), options.prefix, i);
                    $(forms.get(i)).find("*").each(updateElementCallback);
                }
            });
        }
        if ($this.length && showAddButton) {
            var addButton;
            if ($this.prop("tagName") === "TR") {
                // If forms are laid out as table rows, insert the
                // "add" button in a new table row:
                var numCols = this.eq(-1).children().length;
                $parent.append('<tr class="' + options.addCssClass + '"><td colspan="' + numCols + '"><a href="#">' + options.addText + "</a></tr>");
                addButton = $parent.find("tr:last a");
            } else {
                // Otherwise, insert it immediately after the last form:
                $this.filter(":last").after('<div class="' + options.addCssClass + '"><a href="#">' + options.addText + "</a></div>");
                addButton = $this.filter(":last").next().find("a");
            }
            addButton.click(function(e) {
                e.preventDefault();
                var template = $("#" + options.prefix + "-empty");
                var row = template.clone(true);
                row.removeClass(options.emptyCssClass)
                .addClass(options.formCssClass)
                .attr("id", options.prefix + "-" + nextIndex);
                if (row.is("tr")) {
                    // If the forms are laid out in table rows, insert
                    // the remove button into the last table cell:
                    row.children(":last").append('<div><a class="' + options.deleteCssClass + '" href="#">' + options.deleteText + "</a></div>");
                } else if (row.is("ul") || row.is("ol")) {
                    // If they're laid out as an ordered/unordered list,
                    // insert an <li> after the last list item:
                    row.append('<li><a class="' + options.deleteCssClass + '" href="#">' + options.deleteText + "</a></li>");
                } else {
                    // Otherwise, just insert the remove button as the
                    // last child element of the form's container:
                    row.children(":first").append('<span><a class="' + options.deleteCssClass + '" href="#">' + options.deleteText + "</a></span>");
                }
                row.find("*").each(function() {
                    updateElementIndex(this, options.prefix, totalForms.val());
                });
                // Insert the new form when it has been fully edited
                row.insertBefore($(template));

                enableAutocomplete($('input#id_'+row[0].id+'-name'),
                                    '/' + gettext('en') + '/store/product_name/autocomplete/');
                enableAutocomplete($('input#id_'+row[0].id+'-identifier'),
                                    '/' + gettext('en') + '/store/product_asin/autocomplete/');
                enableAutocomplete($('input#id_'+row[0].id+'-upc'),
                                    '/' + gettext('en') + '/store/product_upc/autocomplete/');
                clearSelection($('a#id_'+row[0].id+'-clear'));

                // Update number of total forms
                $(totalForms).val(parseInt(totalForms.val(), 10) + 1);
                nextIndex += 1;
                // Hide add button in case we've hit the max, except we want to add infinitely
                if ((maxForms.val() !== '') && (maxForms.val() - totalForms.val()) <= 0) {
                    addButton.parent().hide();
                }
                // The delete button of each row triggers a bunch of other things
                row.find("a." + options.deleteCssClass).click(function(e1) {
                    e1.preventDefault();
                    // Remove the parent form containing this button:
                    row.remove();
                    nextIndex -= 1;
                    // If a post-delete callback was provided, call it with the deleted form:
                    if (options.removed) {
                        options.removed(row);
                    }
                    $(document).trigger('formset:removed', [row, options.prefix]);
                    // Update the TOTAL_FORMS form count.
                    var forms = $("." + options.formCssClass);
                    $("#id_" + options.prefix + "-TOTAL_FORMS").val(forms.length);
                    // Show add button again once we drop below max
                    if ((maxForms.val() === '') || (maxForms.val() - forms.length) > 0) {
                        addButton.parent().show();
                    }
                    // Also, update names and ids for all remaining form controls
                    // so they remain in sequence:
                    var i, formCount;
                    var updateElementCallback = function() {
                        updateElementIndex(this, options.prefix, i);
                    };
                    for (i = 0, formCount = forms.length; i < formCount; i++) {
                        updateElementIndex($(forms).get(i), options.prefix, i);
                        $(forms.get(i)).find("*").each(updateElementCallback);
                    }
                });
                // If a post-add callback was supplied, call it with the added form:
                if (options.added) {
                    options.added(row);
                }
                $(document).trigger('formset:added', [row, options.prefix]);
            });
        }
        return this;
    };

    /* Setup plugin defaults */
    $.fn.formset.defaults = {
        prefix: "form",          // The form prefix for your django formset
        addText: "add another",      // Text for the add link
        deleteText: "remove",      // Text for the delete link
        addCssClass: "add-row",      // CSS class applied to the add link
        deleteCssClass: "delete-row",  // CSS class applied to the delete link
        emptyCssClass: "empty-row",    // CSS class applied to the empty row
        formCssClass: "dynamic-form",  // CSS class applied to each form in a formset
        added: null,          // Function called each time a new form is added
        removed: null          // Function called each time a form is deleted
    };


    // Tabular inlines ---------------------------------------------------------
    $.fn.tabularFormset = function(options) {
        var $rows = $(this);
        var alternatingRows = function(row) {
            $($rows.selector).not(".add-row").removeClass("row1 row2")
            .filter(":even").addClass("row1").end()
            .filter(":odd").addClass("row2");
        };

        var reinitDateTimeShortCuts = function() {
            // Reinitialize the calendar and clock widgets by force
            if (typeof DateTimeShortcuts !== "undefined") {
                $(".datetimeshortcuts").remove();
                DateTimeShortcuts.init();
            }
        };

        var updateSelectFilter = function() {
            // If any SelectFilter widgets are a part of the new form,
            // instantiate a new SelectFilter instance for it.
            if (typeof SelectFilter !== 'undefined') {
                $('.selectfilter').each(function(index, value) {
                    var namearr = value.name.split('-');
                    SelectFilter.init(value.id, namearr[namearr.length - 1], false);
                });
                $('.selectfilterstacked').each(function(index, value) {
                    var namearr = value.name.split('-');
                    SelectFilter.init(value.id, namearr[namearr.length - 1], true);
                });
            }
        };

        var initPrepopulatedFields = function(row) {
            row.find('.prepopulated_field').each(function() {
                var field = $(this),
                    input = field.find('input, select, textarea'),
                    dependency_list = input.data('dependency_list') || [],
                    dependencies = [];
                $.each(dependency_list, function(i, field_name) {
                    dependencies.push('#' + row.find('.field-' + field_name).find('input, select, textarea').attr('id'));
                });
                if (dependencies.length) {
                    input.prepopulate(dependencies, input.attr('maxlength'));
                }
            });
        };

        $rows.formset({
            prefix: options.prefix,
            addText: options.addText,
            formCssClass: "dynamic-" + options.prefix,
            deleteCssClass: "inline-deletelink",
            deleteText: options.deleteText,
            emptyCssClass: "empty-form",
            removed: alternatingRows,
            added: function(row) {
                initPrepopulatedFields(row);
                reinitDateTimeShortCuts();
                updateSelectFilter();
                alternatingRows(row);
            }
        });

        return $rows;
    };

    // Stacked inlines ---------------------------------------------------------
    $.fn.stackedFormset = function(options) {
        var $rows = $(this);
        var updateInlineLabel = function(row) {
            $($rows.selector).find(".inline_label").each(function(i) {
                var count = i + 1;
                $(this).html($(this).html().replace(/(#\d+)/g, "#" + count));
            });
        };

        var reinitDateTimeShortCuts = function() {
            // Reinitialize the calendar and clock widgets by force, yuck.
            if (typeof DateTimeShortcuts !== "undefined") {
                $(".datetimeshortcuts").remove();
                DateTimeShortcuts.init();
            }
        };

        var updateSelectFilter = function() {
            // If any SelectFilter widgets were added, instantiate a new instance.
            if (typeof SelectFilter !== "undefined") {
                $(".selectfilter").each(function(index, value) {
                    var namearr = value.name.split('-');
                    SelectFilter.init(value.id, namearr[namearr.length - 1], false);
                });
                $(".selectfilterstacked").each(function(index, value) {
                    var namearr = value.name.split('-');
                    SelectFilter.init(value.id, namearr[namearr.length - 1], true);
                });
            }
        };

        var initPrepopulatedFields = function(row) {
            row.find('.prepopulated_field').each(function() {
                var field = $(this),
                    input = field.find('input, select, textarea'),
                    dependency_list = input.data('dependency_list') || [],
                    dependencies = [];
                $.each(dependency_list, function(i, field_name) {
                    dependencies.push('#' + row.find('.form-row .field-' + field_name).find('input, select, textarea').attr('id'));
                });
                if (dependencies.length) {
                    input.prepopulate(dependencies, input.attr('maxlength'));
                }
            });
        };

        $rows.formset({
            prefix: options.prefix,
            addText: options.addText,
            formCssClass: "dynamic-" + options.prefix,
            deleteCssClass: "inline-deletelink",
            deleteText: options.deleteText,
            emptyCssClass: "empty-form",
            removed: updateInlineLabel,
            added: function(row) {
                initPrepopulatedFields(row);
                reinitDateTimeShortCuts();
                updateSelectFilter();
                updateInlineLabel(row);
            }
        });

        return $rows;
    };

    $(document).ready(function() {
        $(".js-inline-admin-formset").each(function() {
            var data = $(this).data(),
                inlineOptions = data.inlineFormset;
            switch(data.inlineType) {
            case "stacked":
                $(inlineOptions.name + "-group .inline-related").stackedFormset(inlineOptions.options);
                break;
            case "tabular":
                $(inlineOptions.name + "-group .tabular.inline-related tbody tr").tabularFormset(inlineOptions.options);
                break;
            }
        });
    });
})(django.jQuery);
