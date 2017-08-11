function preAddCheck(options)
{
    if(options.prefix === 'product_set')
    {
        try
        {
            var selectedValue = JSON.parse($( '#' + options.prefix + '-autocomplete-selected' ).val());
            if(selectedValue && selectedValue.label !== undefined && selectedValue.value !== undefined && selectedValue.desc !== undefined)
            {
                var add = true;
                $('#' + options.prefix + '-group .inline-related .inline-row-key').each(function()
                {
                    if($(this).val() === '' + selectedValue.value)
                    {
                        add = false;
                        return false;
                    }
                });
                return add;
            }
        }
        catch (ex)
        {}
        return false;
    }
    return true;
}

function addInlineRow(row, options)
{
    if(options.prefix === 'product_set')
    {
        try
        {
            var selectedValue = JSON.parse($( '#' + options.prefix + '-autocomplete-selected' ).val());
            row.find('td').each(function(index)
            {
                switch(index)
                {
                    case 0:
                        $(this).find('.inline-row-key').val(selectedValue.value);
                        $(this).append(selectedValue.value);
                        break;
                    case 1:
                        $(this).append(selectedValue.label);
                        break;
                    case 2:
                        $(this).append(selectedValue.desc);
                        break;
                    case 3:
                        $(this).append(selectedValue.bb);
                        break;
                    case 4:
                        var element = $(this).find('input.quantity_validate');
                        element.val(selectedValue.qty);
                        addQuantityEvent(element, options.prefix);
                        return false;
                }
            });
            calculateTotalProducts(options.prefix);
            $( '#' + options.prefix + '-autocomplete' ).val('');
        }
        catch(ex)
        {
            row.remove();
        }
    }

    if(options.prefix === 'warehouse_set')
    {
        var whcke = row.find('textarea.wh-ck');
        if(whcke[0])
        {
            whcke.each(function ()
            {
                row.find('#cke_' + $(this).attr('id')).remove();
                CKEDITOR.replace($(this).attr('id'),
                {
                    customConfig: 'my_config.js'
                });
            });
        }
    }
}

function addQuantityEvent(element, prefix)
{
    element.blur(function(e)
    {
        calculateTotalProducts(prefix);
    });
}

function calculateTotalProducts(prefix)
{
    var total = 0;
    var items = [];
    $('#' + prefix + '-group .inline-related .quantity_validate').each(function()
    {
        if($(this).attr('id').indexOf('__prefix__') < 0)
        {
            items.push(
            {
                p: $(this).closest('.inline-related').find('.inline-row-key').val(),
                q: Number($(this).val())
            });
            total += Number($(this).val());
        }
    });
    $('#totalCost').data('items', JSON.stringify(items));
    var previousValue = $('#totalProducts')[0].innerHTML;
    $('#totalProducts')[0].innerHTML = total;
    if(previousValue !== ''+total)
    {
        $('#totalCost')[0].innerHTML = '-';
    }
}

function removedInlineRow(row, options)
{
    if(options.prefix === 'product_set')
    {
        calculateTotalProducts(options.prefix);
    }
}

function formInitialized(options)
{
    if(options.prefix === 'product_set')
    {
        $('#' + options.prefix + '-group .inline-related .quantity_validate').each(function()
        {
            addQuantityEvent($(this), options.prefix);
        });
        calculateTotalProducts(options.prefix);
        $('#btn-calculate-shipment').click(function(e)
        {
            e.preventDefault();
            $.ajax(
            {
                method: 'GET',
                url: '/shipment/calculate/',
                data: 'items=' + $('#totalCost').data('items')
            })
            .done(function( obj )
            {
                $('#totalCost')[0].innerHTML = obj.cost;
            });
        });
    }
}
