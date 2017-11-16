

(function(globals) {

  var django = globals.django || (globals.django = {});

  
  django.pluralidx = function(n) {
    var v=(n > 1);
    if (typeof(v) == 'boolean') {
      return v ? 1 : 0;
    } else {
      return v;
    }
  };
  

  /* gettext library */

  django.catalog = django.catalog || {};
  
  var newcatalog = {
    "%(sel)s of %(cnt)s selected": [
      "%(sel)s de %(cnt)s selecionado",
      "%(sel)s de %(cnt)s selecionados"
    ],
    "/login": "/entrar",
    "/user/password/forgot/": "/usuario/senha/esqueceu/",
    "6 a.m.": "6 a.m.",
    "6 p.m.": "6 p.m.",
    "Access denied": "Acesso negado",
    "Available %s": "Dispon\u00edvel %s",
    "Cancel": "Cancelar",
    "Choose": "Escolher",
    "Choose a Date": "Escolha a Data",
    "Choose a Time": "Escolha a Hora",
    "Choose a time": "Escolha a hora",
    "Choose all": "Escolher todos",
    "Chosen %s": "Escolhido %s",
    "Click to choose all %s at once.": "Clique para escolher todos os %s de uma vez.",
    "Click to remove all chosen %s at once.": "Clique para remover todos os %s escolhidos de uma vez.",
    "Error": "Erro",
    "Expiration date": "Validade",
    "Filter": "Filtrar",
    "Hide": "Ocultar",
    "In case of more than one warehouse, type in here the products and quantity for this warehouse and then click to add another warehouse...": "Caso haja mais de um local de envio, digite aqui os produtos e as respectivas quantidades que dever\u00e3o ser enviados para esta warehouse. Em seguida, abaixo, adicione o outro local...",
    "Midnight": "Meia-noite",
    "Noon": "Meio-dia",
    "Note: You are %s hour ahead of server time.": [
      "Nota: O seu fuso hor\u00e1rio est\u00e1 %s hora adiantado em rela\u00e7\u00e3o ao servidor.",
      "Nota: O seu fuso hor\u00e1rio est\u00e1 %s horas adiantado em rela\u00e7\u00e3o ao servidor."
    ],
    "Note: You are %s hour behind server time.": [
      "Nota: O use fuso hor\u00e1rio est\u00e1 %s hora atrasado em rela\u00e7\u00e3o ao servidor.",
      "Nota: O use fuso hor\u00e1rio est\u00e1 %s horas atrasado em rela\u00e7\u00e3o ao servidor."
    ],
    "Now": "Agora",
    "Pick ticket": "Localiza\u00e7\u00e3o na Warehouse",
    "Please enter a date greater than {1}.": "Informe uma data maior que a {1}.",
    "Please enter a date less than or equal to today.": "Informe uma data menor ou igual a de hoje.",
    "Please enter a number greater than zero.": "Informe um n\u00famero maior que zero.",
    "Please enter a valid date.": "Informe uma data v\u00e1lida.",
    "Please enter a valid email address.": "Informe um e-mail v\u00e1lido.",
    "Please enter at least 6 characters.": "Informe ao menos 6 caracteres.",
    "Please enter the same value again.": "Informe o mesmo valor.",
    "Purchase date": "Data da compra",
    "Remove": "Remover",
    "Remove all": "Remover todos",
    "Required field.": "Campo obrigat\u00f3rio.",
    "See instructions for valid format.": "Consulte as instru\u00e7\u00f5es de formato v\u00e1lido.",
    "Show": "Mostrar",
    "Sorry but we couldn't send your message, try again in a moment.": "Desculpe no momento n\u00e3o foi poss\u00edvel enviar sua mensagem, tente novamente em instantes.",
    "Sorry, but there seems to be some inconsistencies. Please reload the page and try again.": "Desculpe, foi encontrada alguma inconsist\u00eancia nos dados. Por favor, recarregue a p\u00e1gina e tente novamente.",
    "Sorry, but this item is unavailable.": "Desculpe, mas este item se encontra indispon\u00edvel.",
    "Sorry, we are unable to process your operation. Please reload the page and try again.": "Desculpe, n\u00e3o foi poss\u00edvel realizar sua opera\u00e7\u00e3o. Por favor, recarregue a p\u00e1gina e tente novamente.",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Esta \u00e9 a lista de %s dispon\u00edveis. Poder\u00e1 escolher alguns, selecionando-os na caixa abaixo e clicando na seta \"Escolher\" entre as duas caixas.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Esta \u00e9 a lista de %s escolhidos. Poder\u00e1 remover alguns, selecionando-os na caixa abaixo e clicando na seta \"Remover\" entre as duas caixas.",
    "Today": "Hoje",
    "Tomorrow": "Amanh\u00e3",
    "Type into this box to filter down the list of available %s.": "Digite nesta caixa para filtrar a lista de %s dispon\u00edveis.",
    "Unable to save, fix errors above to continue.": "N\u00e3o foi poss\u00edvel criar seu envio, corrija os erros destacados acima para continuar.",
    "Yesterday": "Ontem",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Selecionou uma a\u00e7\u00e3o mas ainda n\u00e3o guardou as mudan\u00e7as dos campos individuais. Provavelmente querer\u00e1 o bot\u00e3o Ir ao inv\u00e9s do bot\u00e3o Guardar.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Selecionou uma a\u00e7\u00e3o mas ainda n\u00e3o guardou as mudan\u00e7as dos campos individuais. Carregue em OK para gravar. Precisar\u00e1 de correr de novo a a\u00e7\u00e3o.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Tem mudan\u00e7as por guardar nos campos individuais. Se usar uma a\u00e7\u00e3o, as suas mudan\u00e7as por guardar ser\u00e3o perdidas.",
    "You must add products to this shipment.": "\u00c9 preciso adicionar produtos a este envio.",
    "Your message has been sent. Thank you for your contact.": "Mensagem enviada, obrigado pelo seu contato.",
    "en": "pt",
    "en-US": "pt-BR",
    "mm/dd/yy": "dd/mm/yy"
  };
  for (var key in newcatalog) {
    django.catalog[key] = newcatalog[key];
  }
  

  if (!django.jsi18n_initialized) {
    django.gettext = function(msgid) {
      var value = django.catalog[msgid];
      if (typeof(value) == 'undefined') {
        return msgid;
      } else {
        return (typeof(value) == 'string') ? value : value[0];
      }
    };

    django.ngettext = function(singular, plural, count) {
      var value = django.catalog[singular];
      if (typeof(value) == 'undefined') {
        return (count == 1) ? singular : plural;
      } else {
        return value[django.pluralidx(count)];
      }
    };

    django.gettext_noop = function(msgid) { return msgid; };

    django.pgettext = function(context, msgid) {
      var value = django.gettext(context + '\x04' + msgid);
      if (value.indexOf('\x04') != -1) {
        value = msgid;
      }
      return value;
    };

    django.npgettext = function(context, singular, plural, count) {
      var value = django.ngettext(context + '\x04' + singular, context + '\x04' + plural, count);
      if (value.indexOf('\x04') != -1) {
        value = django.ngettext(singular, plural, count);
      }
      return value;
    };

    django.interpolate = function(fmt, obj, named) {
      if (named) {
        return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
      } else {
        return fmt.replace(/%s/g, function(match){return String(obj.shift())});
      }
    };


    /* formatting library */

    django.formats = {
    "DATETIME_FORMAT": "j \\d\\e F \\d\\e Y \u00e0\\s H:i",
    "DATETIME_INPUT_FORMATS": [
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d",
      "%d/%m/%Y %H:%M:%S",
      "%d/%m/%Y %H:%M:%S.%f",
      "%d/%m/%Y %H:%M",
      "%d/%m/%Y",
      "%d/%m/%y %H:%M:%S",
      "%d/%m/%y %H:%M:%S.%f",
      "%d/%m/%y %H:%M",
      "%d/%m/%y"
    ],
    "DATE_FORMAT": "j \\d\\e F \\d\\e Y",
    "DATE_INPUT_FORMATS": [
      "%Y-%m-%d",
      "%d/%m/%Y",
      "%d/%m/%y"
    ],
    "DECIMAL_SEPARATOR": ",",
    "FIRST_DAY_OF_WEEK": "0",
    "MONTH_DAY_FORMAT": "j \\d\\e F",
    "NUMBER_GROUPING": "3",
    "SHORT_DATETIME_FORMAT": "d/m/Y H:i",
    "SHORT_DATE_FORMAT": "d/m/Y",
    "THOUSAND_SEPARATOR": ".",
    "TIME_FORMAT": "H:i",
    "TIME_INPUT_FORMATS": [
      "%H:%M:%S",
      "%H:%M:%S.%f",
      "%H:%M"
    ],
    "YEAR_MONTH_FORMAT": "F \\d\\e Y"
  };

    django.get_format = function(format_type) {
      var value = django.formats[format_type];
      if (typeof(value) == 'undefined') {
        return format_type;
      } else {
        return value;
      }
    };

    /* add to global namespace */
    globals.pluralidx = django.pluralidx;
    globals.gettext = django.gettext;
    globals.ngettext = django.ngettext;
    globals.gettext_noop = django.gettext_noop;
    globals.pgettext = django.pgettext;
    globals.npgettext = django.npgettext;
    globals.interpolate = django.interpolate;
    globals.get_format = django.get_format;

    django.jsi18n_initialized = true;
  }

}(this));

