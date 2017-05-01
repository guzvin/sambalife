function preAddCheck(options)
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

function addInlineRow(row, prefix)
{
    try
    {
        var selectedValue = JSON.parse($( '#' + prefix + '-autocomplete-selected' ).val());
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
                    var element = $(this).find('input.quantity_validate');
                    element.val(selectedValue.qty);
                    addQuantityEvent(element, prefix);
                    return false;
            }
        });
        calculateTotalProducts(prefix);
        $( '#' + prefix + '-autocomplete' ).val('');
    }
    catch(ex)
    {
        row.remove();
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
    $('#' + prefix + '-group .inline-related .quantity_validate').each(function()
    {
        total += Number($(this).val());
    });
    var previousValue = $('#totalProducts')[0].innerHTML;
    $('#totalProducts')[0].innerHTML = total;
    if(previousValue !== ''+total)
    {
        $('#totalCost')[0].innerHTML = '-';
    }
}

function formInitialized(options)
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
            data: 'items=' + $('#totalProducts')[0].innerHTML
        })
        .done(function( obj )
        {
            $('#totalCost')[0].innerHTML = obj.cost;
        });
    });
}