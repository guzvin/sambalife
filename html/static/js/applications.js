// Agency Theme JavaScript

(function($)
{
    'use strict';
    function getCookie(name)
    {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '')
        {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++)
            {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '='))
                {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function csrfSafeMethod(method)
    {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    $.ajaxSetup(
    {
        beforeSend: function(xhr, settings)
        {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain)
            {
                xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
            }
        }
    });

    $(document).ajaxError(function( event, jqXHR, settings, thrownError )
    {
        if(jqXHR.responseJSON && jqXHR.responseJSON.terms_and_conditions)
        {
            $('#terms_conditions').modal('show');
        }
    });

    // jQuery for page scrolling feature - requires jQuery Easing plugin
    $('a.page-scroll').bind('click', function(event)
    {
        var $anchor = $(this);
        $('html, body').stop().animate(
        {
            scrollTop: ($($anchor.attr('href')).offset().top - 50)
        }, 1250, 'easeInOutExpo');
        event.preventDefault();
    });

    if($('body.index').scrollspy)
    {
        // Highlight the top nav as scrolling occurs
        $('body.index').scrollspy(
        {
            target: '.navbar-fixed-top',
            offset: 51
        });
    }

    if($('body.index-home #mainNav').affix)
    {
        // Offset for Main Navigation
        $('body.index-home #mainNav').affix(
        {
            offset:
            {
                top: 100
            }
        });
    }

    $('.mudar-status').click(function()
    {
        var elem = $(this).parent('td').find('.contem-status');
        if(elem.is(':visible'))
            elem.hide();
        else
            elem.show();
    });
    
    $('.fechar').click(function()
    {
        $(this).closest('.contem-status').hide();
    });
    
    if($.datepicker){
        $.datepicker.regional['pt-BR'] =
        {
            closeText: 'Fechar',
            prevText: '&#x3c;Anterior',
            nextText: 'Pr&oacute;ximo&#x3e;',
            currentText: 'Hoje',
            monthNames: ['Janeiro','Fevereiro','Mar&ccedil;o','Abril','Maio','Junho',
            'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'],
            monthNamesShort: ['Jan','Fev','Mar','Abr','Mai','Jun',
            'Jul','Ago','Set','Out','Nov','Dez'],
            dayNames: ['Domingo','Segunda-feira','Ter&ccedil;a-feira','Quarta-feira','Quinta-feira','Sexta-feira','Sabado'],
            dayNamesShort: ['Dom','Seg','Ter','Qua','Qui','Sex','Sab'],
            dayNamesMin: ['Dom','Seg','Ter','Qua','Qui','Sex','Sab'],
            weekHeader: 'Sm',
            dateFormat: 'dd/mm/yy',
            firstDay: 0,
            isRTL: false,
            showMonthAfterYear: false,
            yearSuffix: ''
        };

        $.datepicker.setDefaults($.datepicker.regional[gettext('en-US')]);

        $( ".datepicker" ).datepicker();
    }

    if($("[data-toggle='tooltip']").tooltip)
    {
        $("[data-toggle='tooltip']").tooltip(
        {
            placement : 'top'
        });
    }

    if($.validator)
    {
        $.validator.methods.passwordFormat = function( value, element )
        {
            return this.optional( element ) || (/[A-Z]/.test(value)
                                                && /[a-z]/.test(value)
                                                && /\d/.test(value)
                                                && /[^a-zA-Z\d]/.test(value));
        };

        $.validator.addMethod('positiveNumber', function (value, element)
        {
            if (this.optional(element))
            {
                return true;
            }
            try
            {
                if(parseFloat(value) > 0)
                {
                    return !isNaN(value);
                }
            }
            catch (err)
            {}
            return false;
        });

        if($.datepicker)
        {
            $.validator.addMethod('date', function (value, element)
            {
                if (this.optional(element))
                {
                    return true;
                }
                var valid = true;
                try
                {
                    $.datepicker.parseDate(gettext('mm/dd/yy'), value);
                }
                catch (err)
                {
                    valid = false;
                }
                return valid;
            });
            $.validator.addMethod('dateLessThanOrEqualNow', function (value, element)
            {
                if (this.optional(element))
                {
                    return true;
                }
                var valid = true;
                try
                {
                    return $.datepicker.parseDate(gettext('mm/dd/yy'), value) <= new Date();
                }
                catch (err)
                {
                    valid = false;
                }
                return valid;
            });
            $.validator.addMethod('dateGreaterThan', function (value, element, params)
            {
                if (this.optional(element))
                {
                    return true;
                }
                var valid = true;
                try
                {
                    var dateToCompare = $.datepicker.parseDate(gettext('mm/dd/yy'), $(params[0]).val());
                    if(!dateToCompare)
                    {
                        throw 'null';
                    }
                    try
                    {
                        return $.datepicker.parseDate(gettext('mm/dd/yy'), value) > dateToCompare;
                    }
                    catch (err)
                    {
                        valid = false;
                    }
                }
                catch (err)
                {
                    valid = false;
                }
                return valid;
            }, $.validator.format(gettext('Please enter a date greater than {1}.')));
            $.validator.addMethod('productsNotEmpty', function (value, element)
            {
                return $(element).val() === '1';
            });
        }

        $.extend(
            $.validator.messages,
            {
                required: gettext('Required field.'),
                minlength: gettext('Please enter at least 6 characters.'),
                equalTo: gettext('Please enter the same value again.'),
                passwordFormat: gettext('See instructions for valid format.'),
                email: gettext('Please enter a valid email address.'),
                date: gettext('Please enter a valid date.'),
                dateLessThanOrEqualNow: gettext('Please enter a date less than or equal to today.'),
                positiveNumber: gettext('Please enter a number greater than zero.'),
                productsNotEmpty: gettext('You must add products to this shipment.'),
            }
        );
    }

    if($('form#form-add-user')[0])
    {
        $('button#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
        });

        $('form#form-add-user').validate(
        {
            rules:
            {
                first_name: { required: true },
                last_name: { required: true },
                email: { required: true },
                doc_number: { required: true },
                cell_phone: { required: true },
                country: { required: true },
                address_1: { required: true },
                city: { required: true },
                state: { required: true },
                zipcode: { required: true },
                password:
                {
                    required: true,
                },
                password_confirmation:
                {
                    required: true,
                    equalTo: '#senha'
                },
                terms: { required: true },
            },
            errorPlacement: function(error, element)
            {
                if (element.attr('name') == 'terms')
                {
                    error.insertAfter(element.parent());
                }
                else
                {
                    error.insertAfter(element);
                }
            },
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('button#send-btn').removeClass('nosubmit');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });
    }

    if($('form#form-login')[0])
    {
        $('input#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
            $('form#form-login').attr('action', '/login/');
        });

        $('a#forgot-password-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
            $('form#form-login').attr('action', '/user/password/forgot/');
            $('form#form-login').submit();
        });

        $('form#form-login').validate(
        {
            errorPlacement: function(error, element)
            {
                var breakLine = $('<br></br>');
                breakLine.insertAfter(element);
                error.insertAfter(breakLine);
                breakLine.clone().insertAfter(error);
            },
            rules:
            {
                login: { required: true },
                password:
                {
                    required:
                    {
                        depends: function(element)
                        {
                          return $('form#form-login').attr('action') === '/login';
                        }
                    },
                },
            },
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('input#send-btn').removeClass('nosubmit');
                $('a#forgot-password-btn').removeClass('nosubmit');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });
    }

    if($('form#form-reset-password')[0])
    {
        $('button#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
        });

        $('form#form-reset-password').validate(
        {
            rules:
            {
                email: { required: true },
                password:
                {
                    required: true,
                },
                password_confirmation:
                {
                    required: true,
                    equalTo: '#senha'
                },
            },
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('button#send-btn').removeClass('nosubmit');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });
    }

    if($('form#form-add-product')[0])
    {
        $('button#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
        });

        $('form#form-add-product').validate(
        {
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('button#send-btn').removeClass('nosubmit');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });
        $('.name_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true
            });
        });
        $('.quantity_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                positiveNumber: true,
            });
        });
        $('.quantity_partial_validate').each(function ()
        {
            $(this).rules('add',
            {
                positiveNumber: true,
            });
        });
        $('.send_date_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                date: true,
                dateLessThanOrEqualNow: true,
            });
        });
        $('.edd_date_validate').each(function ()
        {
            $(this).rules('add',
            {
                date: true,
                dateGreaterThan: ['.send_date_validate', gettext('Purchase date')],
            });
        });
        $('.best_before_validate').each(function ()
        {
            $(this).rules('add',
            {
                date: true,
            });
        });
        $('.condition_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
    }

    $('.send-btn-async').click(function(e)
    {
        var form = $(this).closest('form.form-change-status');
        var pid = form.find('input.product-id').val();
        if(form.attr('id').split('-')[3] === pid)
        {
            var radioChecked = form.find('input:radio:checked');
            if(radioChecked[0])
            {
                var tr = form.closest('tr');
                var quantityColumn = tr.find('td.row-quantity');
                var pickTicketColumn = tr.find('td.row-pick-ticket-display');
                var inputPartial = tr.find('input.row-qty-partial');
                var currentPartial = inputPartial.data('current-partial');
                var newPartialValue = inputPartial.val();
                var inputBestBefore = tr.find('input.row-best-before');
                var currentBestBefore = inputBestBefore.data('best-before')
                var newBestBeforeValue = inputBestBefore.val();
                var selectActualCondition = tr.find('select.row-actual-condition');
                var currentActualCondition = selectActualCondition.data('actual-condition')
                var newActualConditionValue = selectActualCondition.val();
                var inputConditionComments = tr.find('input.row-condition-comments');
                var currentConditionComments = inputConditionComments.data('condition-comments')
                var newConditionCommentsValue = inputConditionComments.val();

                var inputPickTicket = tr.find('input.row-pick-ticket');
                var currentPickTicket = inputPickTicket.data('pick-ticket')
                var newPickTicketValue = inputPickTicket.val();

                var checkedValue = radioChecked.val();
                var currentValue = radioChecked.data('current-status');
                if(''+checkedValue !== ''+currentValue || ''+currentPartial !== ''+newPartialValue || ''+currentBestBefore != ''+newBestBeforeValue
                || ''+currentActualCondition != ''+newActualConditionValue || ''+currentConditionComments != ''+newConditionCommentsValue
                || ''+currentPickTicket != ''+newPickTicketValue)
                {
                    var $this = $(this);
                    if($this.hasClass('nosubmit'))
                    {
                        e.preventDefault();
                        return false;
                    }
                    $this.addClass('nosubmit');
                    $('.loading').show();
                    $.ajax(
                    {
                        method: 'PUT',
                        url: '/product/edit/status/' + pid + '.json',
                        data: form.serialize()
                    })
                    .done(function( obj )
                    {
                        $('span#product-status-display-'+obj.product.id).text(obj.product.status_display);
                        form.find('input:radio').data('current-status', obj.product.status);
                        inputPartial.data('current-partial', obj.product.quantity_partial);
                        inputBestBefore.data('best-before', obj.product.best_before);
                        selectActualCondition.data('actual-condition', obj.product.actual_condition);
                        inputConditionComments.data('condition-comments', obj.product.condition_comments);
                        inputPickTicket.data('pick-ticket', obj.product.pick_ticket);
                        if(obj.product.show_check && obj.product.status === SHIPMENT_STATUS_IN_STOCK && obj.product.quantity >= 0)
                        {
                            var checkColumn = $('span#product-status-display-'+obj.product.id).closest('td').next();
                            if(!checkColumn.find('input[type="checkbox"]')[0])
                            {
                                var checkbox = $('<input type="checkbox" name="shipment_product" value="' + obj.product.id + '" id="shipment-' + obj.product.id + '" class="shipment-product" />');
                                checkColumn.append(checkbox);
                            }
                        }
                        else
                        {
                            $('span#product-status-display-'+obj.product.id).closest('td').next()[0].innerHTML = '';
                        }
                        var qtyInfo = obj.product.quantity;
                        if(parseInt(obj.product.quantity_partial) && !isNaN(obj.product.quantity_partial) && obj.product.quantity !== obj.product.quantity_partial)
                        {
                            qtyInfo += ' ('+obj.product.quantity_partial+')';
                        }
                        quantityColumn.find('span.row-quantity-display')[0].innerHTML = qtyInfo;
                        var bestBefore = obj.product.best_before;
                        var rowBestBefore = quantityColumn.find('span.row-bestbefore-display');
                        if(bestBefore !== '')
                        {
                            if(rowBestBefore[0])
                            {
                                rowBestBefore[0].innerHTML = '<br>' + gettext('Expiration date') + ':<br>' + bestBefore;
                            }
                            else
                            {
                                quantityColumn.append($('<span class="row-bestbefore-display"><br>' + gettext('Expiration date') + ':<br>' + bestBefore + '</span>'));
                            }
                        }
                        else
                        {
                            if(rowBestBefore[0])
                            {
                                rowBestBefore.remove();
                            }
                        }
                        var pickTicket = obj.product.pick_ticket;
                        $('span.help.fa-thumb-tack').remove();
                        if(pickTicket !== '')
                        {
                            pickTicketColumn.append($('<span class="help help-tooltip fa fa-thumb-tack" title="' + gettext('Pick ticket') + ': ' + pickTicket + '"></span>'));
                        }
                        form.closest('.contem-status').hide();
                    })
                    .fail(function(jqXHR, textStatus, errorThrown)
                    {
                        if(jqXHR.responseJSON && jqXHR.responseJSON.terms_and_conditions)
                        {
                            return;
                        }
                        alert(jqXHR.responseJSON.error);
                    })
                    .always(function()
                    {
                        $('.loading').hide();
                        $this.removeClass('nosubmit');
                    });
                }
            }
        }
        return false;
    });

    $('.send-btn-delete, #cancel-btn').click(function()
    {
        $('#confirmacao-exclusao').modal('show');
    });

    $('.open-adress').click(function()
    {
        $('#box-adress').modal('show');
    });

    if($('#form-archive-shipment')[0])
    {
        if($('#archive-btn')[0])
        {
            $('#archive-btn').click(function()
            {
                $('.loading').show();
                $('#form-archive-shipment').submit();
            });
        }
        else if($('#restore-btn')[0])
        {
            $('#restore-btn').click(function()
            {
                $('.loading').show();
                $('#form-archive-shipment').submit();
            });
        }
    }

    $('.privatebtn').click(function()
    {
        $('#portfolioModal1').modal('show');
    });

    $('#privatebtn').click(function()
    {
        $('#portfolioModal1').modal('show');
    });

    if($('#form-add-shipment')[0])
    {
        var shipmentProducts = sessionStorage.getItem('shipment_products');
        if(!shipmentProducts)
        {
            shipmentProducts = '{}'
        }
        shipmentProducts = JSON.parse(shipmentProducts);
        $('.shipment-product').each(function()
        {
            if(shipmentProducts['p' + $(this).val()])
            {
                this.checked = true;
            }
            else
            {
                this.checked = false;
            }
        });

        var shipmentForm = $('#form-add-shipment');
        $('.shipment-product').change(function()
        {
            if(this.checked)
            {
                shipmentProducts['p' + $(this).val()] = $(this).val();
            }
            else
            {
                delete shipmentProducts['p' + $(this).val()];
            }
            sessionStorage.setItem('shipment_products', JSON.stringify(shipmentProducts));
        });
        $('#btn-add-shipment, #btn-add-merchant-shipment').click(function()
        {
            var get = true;
            for(var shipmentProduct in shipmentProducts)
            {
                var checkedProduct = $('<input type="hidden" name="shipment_product"></input>');
                checkedProduct.val(shipmentProducts[shipmentProduct]);
                checkedProduct.appendTo(shipmentForm);
                get = false;
            }
            if(get)
            {
                window.location.href = $(this).data('action-url');
            }
            else
            {
//                sessionStorage.removeItem('shipment_products');
                shipmentForm.attr('action', $(this).data('action-url'));
                shipmentForm.submit();
            }
        });
    }
    else
    {
//        sessionStorage.removeItem('shipment_products');
    }

    if($('form#form-save-shipment')[0])
    {
        $('button#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
        });

        $('form#form-save-shipment').validate(
        {
            ignore: '#id_product_set-__prefix__-quantity, #id_warehouse_set-__prefix__-name',
            submitHandler: function(form)
            {
                $('.loading').show();
                sessionStorage.removeItem('shipment_products');
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('button#send-btn').removeClass('nosubmit');
                $('<label id="send-btn-error" class="error" for="send-btn">' + gettext('Unable to save, fix errors above to continue.') + '</label>').insertAfter('button#send-btn');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });

        window.addRule = function(element, rules)
        {
            element.rules('add', rules);
        }

        $('.quantity_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                positiveNumber: true,
            });
        });
        $('.pdf_1-validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
        $('.warehouse_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
        $('.products_validate').each(function ()
        {
            $(this).rules('add',
            {
                productsNotEmpty: true,
            });
        });
    }

    if($('form.form-filter')[0] && $('ul.pagination')[0])
    {
        $('a.pagination-page').click(function(e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
            var data = $(this).data();
            var selectedPage = $('input#selected-page');
            if(selectedPage[0])
            {
                selectedPage.val(data.page);
            }
            else
            {
                var hidden = $('<input type="hidden" name="page" value="' + data.page + '" id="selected-page" />');
                $('form.form-filter').append(hidden);
            }
            $('form.form-filter').submit();
        });
        $('form.form-filter').find('button[type="submit"]').click(function(e)
        {
            e.preventDefault();
            if($(this).hasClass('nosubmit'))
            {
                return false;
            }
            $(this).addClass('nosubmit');
            var selectedPage = $('input#selected-page');
            if(selectedPage[0])
            {
                selectedPage.remove();
            }
            $('form.form-filter').submit();
        });
    }

    if($('form#form-add-package')[0])
    {
        $('a#send-btn-1').on('click', function (e)
        {
            e.preventDefault();
            if($(this).hasClass('nosubmit'))
            {
                return false;
            }
            $(this).addClass('nosubmit');
            $('form#form-add-package').submit();
        });

        $('form#form-add-package').validate(
        {
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('a#send-btn-1').removeClass('nosubmit');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });

        window.addRule = function(element, rules)
        {
            element.rules('add', rules);
        }

        $('input.required-validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
        $('input.required-number-validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                positiveNumber: true,
            });
        });
    }

    $('a.delete-product-shipment').each(function()
    {
        $(this).click(function(e)
        {
            e.preventDefault();
            var tr = $(this).closest('tr');
            var form = $(this).closest('form');
            $.ajax(
            {
                method: 'DELETE',
                url: '/shipment/delete/product.json',
                data: form.serialize(),
                statusCode:
                {
                    400: function(jqXHR, textStatus, errorThrown)
                    {
                        if(jqXHR.responseJSON && jqXHR.responseJSON.terms_and_conditions)
                        {
                            return;
                        }
                        var body = gettext('Sorry, but there seems to be some inconsistencies. Please reload the page and try again.');
                        assembleModal(gettext('Error'), body);
                    },
                    403: function()
                    {
                        var body = gettext('Access denied');
                        assembleModal(gettext('Error'), body);
                    },
                    500: function()
                    {
                        var body = gettext('Sorry, we are unable to process your operation. Please reload the page and try again.');
                        assembleModal(gettext('Error'), body);
                    }
                }
            })
            .done(function( obj )
            {
                if(obj.redirect)
                {
                    window.location.href = obj.redirect;
                    $('.loading').show();
                    return;
                }
                tr.remove();
                $('#totalProducts')[0].innerHTML = obj.items;
                $('#totalCost')[0].innerHTML = obj.cost;
            });
        });
    });

    if($('form#form-upload-file')[0])
    {
        $('a#send-btn-3').on('click', function (e)
        {
            e.preventDefault();
            if($(this).hasClass('nosubmit'))
            {
                return false;
            }
            $(this).addClass('nosubmit');
            $('form#form-upload-file').submit();
        });

        $('form#form-upload-file').validate(
        {
            submitHandler: function(form)
            {
                $('.loading').show();
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('a#send-btn-3').removeClass('nosubmit');
                $('a#send-btn-5').removeClass('nosubmit');
                $('.loading').hide();
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });
        if($('input[type="hidden"][name="add_package_file"]')[0] && $('input[type="hidden"][name="edit_package_warehouse"]')[0] === undefined)
        {
            $('.pdf_2-validate').each(function ()
            {
                $(this).rules('add',
                {
                    required: true,
                });
            });
        }
    }

    if($('input#payment_button')[0])
    {
        $('input#payment_button').click(function(e)
        {
            e.preventDefault();
            var $this = $(this);
            $.ajax(
            {
                method: 'GET',
                url: '/shipment/pay/' + $this.data('generic'),
                statusCode:
                {
                    400: function(jqXHR, textStatus, errorThrown)
                    {
                        if(jqXHR.responseText)
                        {
                            $('html')[0].innerHTML = jqXHR.responseText;
                            return;
                        }
                        var body = gettext('Sorry, but there seems to be some inconsistencies. Please reload the page and try again.');
                        assembleModal(gettext('Error'), body);
                    },
                    403: function()
                    {
                        var body = gettext('Access denied');
                        assembleModal(gettext('Error'), body);
                    },
                    500: function()
                    {
                        var body = gettext('Sorry, we are unable to process your operation. Please reload the page and try again.');
                        assembleModal(gettext('Error'), body);
                    }
                }
            })
            .done(function( obj )
            {
                var paymentFormArea = $('<span id="payment-form-area"></span>').append($(obj));
                paymentFormArea.insertAfter($this);
                var paymentFormArea = $('span#payment-form-area');
                paymentFormArea.find('form').submit();
                paymentFormArea.remove();
            });
        });
    }

    if($('a#send-btn-final')[0])
    {
        $('a#send-btn-final').on('click', function (e)
        {
            e.preventDefault();
            $('#send-shipment-confirmation').modal('show');
            return false;

        });
    }
    if($('button#send-btn-final-confirmation')[0])
    {
        $('button#send-btn-final-confirmation').on('click', function (e)
        {
            e.preventDefault();
            if($(this).hasClass('nosubmit'))
            {
                return false;
            }
            $(this).addClass('nosubmit');
            $('.loading').show();
            $('form#form-upload-file').append('<input type="hidden" name="complete_shipment" value="1"></input>');
            $('form#form-upload-file').submit();
        });
    }
    if($('a#send-btn-5')[0])
    {
        $('a#send-btn-5').on('click', function (e)
        {
            e.preventDefault();
            if($(this).hasClass('nosubmit'))
            {
                return false;
            }
            $(this).addClass('nosubmit');
            $('.loading').show();
            $('form#form-upload-file').submit();
        });
    }

    if($('textarea.wh-ck')[0])
    {
        $('textarea.wh-ck').each(function ()
        {
            CKEDITOR.replace($(this).attr('id'),
            {
                customConfig: 'my_config.js'
            });
        });
    }

    function assembleModal(title, body)
    {
        $('div.modal-content h4.modal-title')[0].innerHTML = title;
        var modalBody = $('div.modal-content div.modal-body');
        modalBody[0].innerHTML = '';
        modalBody.append($('<p>' + body + '</p>'));
        $('#confirmacao').modal('show');
    }

    if($('#terms_conditions')[0])
    {
        $('#terms_conditions').modal('show');
        if($('#terms-conditions-acceptance')[0])
        {
            $('#terms-conditions-acceptance').click(function()
            {
                $.ajax(
                {
                    method: 'POST',
                    url: '/user/accept_terms/',
                })
                .done(function()
                {
                    $('#terms_conditions').modal('hide');
                });
                return false;
            });
        }
    }

    if($('#product_delete_error')[0])
    {
        $('#product_delete_error').modal('show');
    }

    if($('#contactus-form')[0])
    {
        var form = $('form#contactForm');
        $('#contactus-form').click(function (e)
        {
            var $this = $(this);
            if($this.hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $this.addClass('nosubmit');
            $('#contact-us-feedback').prop('class', '');
            $('#contact-us-feedback')[0].innerHTML = '';
            $('.loading').show();

            $.ajax(
            {
                method: 'GET',
                url: '/touch/'
            }).done(function( obj )
            {
                console.log('done');
                $.ajax(
                {
                    method: 'POST',
                    url: '/contactus/',
                    data: form.serialize()
                })
                .done(function( obj )
                {
                    form[0].reset();
                    $('#contact-us-feedback').prop('class', 'contact-us-success');
                    $('#contact-us-feedback')[0].innerHTML = gettext('Your message has been sent. Thank you for your contact.');
                })
                .fail(function(jqXHR, textStatus, errorThrown)
                {
                    $('#contact-us-feedback').prop('class', 'contact-us-failure');
                    $('#contact-us-feedback')[0].innerHTML = gettext('Sorry but we couldn\'t send your message, try again in a moment.');
                })
                .always(function()
                {
                    $('.loading').hide();
                    $this.removeClass('nosubmit');
                });
            })
            .fail(function(jqXHR, textStatus, errorThrown)
            {
                $('#contact-us-feedback').prop('class', 'contact-us-failure');
                $('#contact-us-feedback')[0].innerHTML = gettext('Sorry but we couldn\'t send your message, try again in a moment.');
                $('.loading').hide();
                $this.removeClass('nosubmit');
            });
        });
    }

    if($('form#form-save-merchant-shipment')[0])
    {
        $('button#send-btn').on('click', function (e)
        {
            if($(this).hasClass('nosubmit'))
            {
                e.preventDefault();
                return false;
            }
            $(this).addClass('nosubmit');
        });

        $('form#form-save-merchant-shipment').validate(
        {
            ignore: '#id_product_set-__prefix__-quantity',
            submitHandler: function(form)
            {
                $('.loading').show();
                sessionStorage.removeItem('shipment_products');
                form.submit()
            },
            invalidHandler: function(event, validator)
            {
                $('button#send-btn').removeClass('nosubmit');
                $('<label id="send-btn-error" class="error" for="send-btn">' + gettext('Unable to save, fix errors above to continue.') + '</label>').insertAfter('button#send-btn');
            },
            onfocusout: false,
            onkeyup: false,
            onclick: false
        });

        window.addRule = function(element, rules)
        {
            element.rules('add', rules);
        }

        $('.quantity_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
                positiveNumber: true,
            });
        });
        $('.type_validate').each(function ()
        {
            $(this).rules('add',
            {
                required: true,
            });
        });
        $('.products_validate').each(function ()
        {
            $(this).rules('add',
            {
                productsNotEmpty: true,
            });
        });
    }

    $('.add-pro').click(function()
    {
        var numeroProduto = Number($('.lista-produtos .produto:last-child .num-produto').text()) + 1;

        $('.lista-produtos').append("<div class='produto'>" +
                "<label class='titulo'>Protuto <span class='num-produto'>" + numeroProduto + "</span></label>" +
                 "<div class='form-group col-md-12'>" +
                        "<label for='nome-produto-" + numeroProduto + "'>Nome Produto</label>" +
                        "<input type='text' class='form-control' id='nome-produto-" + numeroProduto + "' placeholder='Digite nome do Produto...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='UPC-" + numeroProduto + "'>UPC / Codigo identificador</label>" +
                   "    <input type='text' class='form-control' id='UPC-" + numeroProduto + "' placeholder='Digite UPC...'>" +
                  "</div><br> " +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='valor-compra-" + numeroProduto + "'>Valor compra</label>" +
                    "    <input type='text' class='form-control' id='valor-compra-" + numeroProduto + "' placeholder='Digite Valor compra...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='Quantidade-" + numeroProduto + "'>Quantidade</label>" +
                    "    <input type='text' class='form-control' id='Quantidade-" + numeroProduto + "' placeholder='Digite Quantidade...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='total-produto-" + numeroProduto + "'>Total a pagar do produto</label>" +
                    "    <input type='text' class='form-control' id='total-produto-" + numeroProduto + "' placeholder='Digite Total a pagar...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='valor-venda-" + numeroProduto + "'>Valor venda</label>" +
                    "    <input type='text' class='form-control' id='valor-venda-" + numeroProduto + "' placeholder='Digite valor venda...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'> " +
                   "     <label for='fba-" + numeroProduto + "'>FBA fee</label>" +
                    "    <input type='text' class='form-control' id='fba-" + numeroProduto + "' placeholder='Digite FBA fee...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='Amazon-" + numeroProduto + "'>Amazon fee</label>" +
                    "    <input type='text' class='form-control' id='Amazon-" + numeroProduto + "' placeholder='Digite Amazon fee...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='envio-" + numeroProduto + "'>Envio para Amazon</label>" +
                    "    <input type='text' class='form-control' id='envio-" + numeroProduto + "' placeholder='Digite Envio...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='Redirecionamento-" + numeroProduto + "'>Redirecionamento</label>" +
                    "    <input type='text' class='form-control' id='Redirecionamento-" + numeroProduto + "' placeholder='Digite Redirecionamento...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='lucro-unidade-" + numeroProduto + "'>Lucro liquido por unidade</label>" +
                    "    <input type='text' class='form-control' id='lucro-unidade-" + numeroProduto + "' placeholder='Digite lucro por unidade...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'>" +
                   "     <label for='lucro-total-" + numeroProduto + "'>Lucro total</label>" +
                    "    <input type='text' class='form-control' id='lucro-total-" + numeroProduto + "' placeholder='Digite Lucro total...'>" +
                  "</div><br>" +
                  "<div class='form-group col-md-6'> " +
                   "     <label for='roi-produto-" + numeroProduto + "'>ROI (%)</label>" +
                    "    <input type='text' class='form-control' id='roi-produto-" + numeroProduto + "' placeholder='Digite ROI...'>" +
                  "</div>" +
                  "<a class='rem-track btn btn-danger' data-toggle='tooltip' title='Remover produto' href='#'><i class='fa fa-fw fa-times'></i> Remover este produto do lote</a>" +
                "</div>");
    });

    //Tabs pagina ajuda

     $("#ajudatab li:eq(0) a").tab('show');

    //Modal tutorial
    $('.abre-tutorial').click(function(){
        $('#tutorial').modal('show');
    });


    //Modal tutorial redirecionamento BR
    $('#video-explicativo-br').click(function(){
        $('#tutorial-br').modal('show');
    });

    //Click radio cadastro de envio brasil
    $(".endereco-cadastro-chk").click(function(){
         var classe = $(this).find("input[type='radio']").attr("class");
         if(classe == "endereco-novo"){
            $(".endereco-novo-form").show();
         }else{
            $(".endereco-novo-form").hide();
         }
    });

    //Edicao de arquivos das etiquetas
    $(".edit-pdf").click(function(){
        $(this).parent().hide();
        $(this).parent().parent().find(".input-content-edit-pdf").show();
    });

    $(".edit-pdf-undo").click(function(){
        $(this).parent().find('input:file').val('')
        $(this).parent().hide();
        $(this).parent().parent().find(".link-download-pdf").show();
    });



})(jQuery); // End of use strict
