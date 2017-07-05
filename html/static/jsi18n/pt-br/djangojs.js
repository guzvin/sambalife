

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
    "6 a.m.": "6 da manh\u00e3",
    "6 p.m.": "6 da tarde",
    "Access denied": "Acesso negado",
    "April": "Abril",
    "August": "Agosto",
    "Available %s": "%s dispon\u00edveis",
    "Cancel": "Cancelar",
    "Choose": "Escolher",
    "Choose a Date": "Escolha uma data",
    "Choose a Time": "Escolha um hor\u00e1rio",
    "Choose a time": "Escolha uma hora",
    "Choose all": "Escolher todos",
    "Chosen %s": "%s escolhido(s)",
    "Click to choose all %s at once.": "Clique para escolher todos os %s de uma s\u00f3 vez",
    "Click to remove all chosen %s at once.": "Clique para remover de uma s\u00f3 vez todos os %s escolhidos.",
    "December": "Dezembro",
    "Error": "Erro",
    "Expiration date": "Validade",
    "February": "Fevereiro",
    "Filter": "Filtro",
    "Hide": "Esconder",
    "In case of more than one warehouse, type in here the products and quantity for this warehouse and then click to add another warehouse...": "Caso haja mais de um local de envio, digite aqui os produtos e as respectivas quantidades que dever\u00e3o ser enviados para esta warehouse. Em seguida, abaixo, adicione o outro local...",
    "January": "Janeiro",
    "July": "Julho",
    "June": "Junho",
    "March": "Mar\u00e7o",
    "May": "Maio",
    "Midnight": "Meia-noite",
    "Noon": "Meio-dia",
    "Note: You are %s hour ahead of server time.": [
      "Nota: Voc\u00ea est\u00e1 %s hora \u00e0 frente do hor\u00e1rio do servidor.",
      "Nota: Voc\u00ea est\u00e1 %s horas \u00e0 frente do hor\u00e1rio do servidor."
    ],
    "Note: You are %s hour behind server time.": [
      "Nota: Voc\u00ea est\u00e1 %s hora atr\u00e1s do tempo do servidor.",
      "Nota: Voc\u00ea est\u00e1 %s horas atr\u00e1s do hor\u00e1rio do servidor."
    ],
    "November": "Novembro",
    "Now": "Agora",
    "October": "Outubro",
    "Please enter a date less than or equal to today.": "Informe uma data menor ou igual a de hoje.",
    "Please enter a number greater than zero.": "Informe um n\u00famero maior que zero.",
    "Please enter a valid date.": "Informe uma data v\u00e1lida.",
    "Please enter a valid email address.": "Informe um e-mail v\u00e1lido.",
    "Please enter at least 6 characters.": "Informe ao menos 6 caracteres.",
    "Please enter the same value again.": "Informe o mesmo valor.",
    "Remove": "Remover",
    "Remove all": "Remover todos",
    "Required field.": "Campo obrigat\u00f3rio.",
    "See instructions for valid format.": "Consulte as instru\u00e7\u00f5es de formato v\u00e1lido.",
    "September": "Setembro",
    "Show": "Mostrar",
    "Sorry, but there seems to be some inconsistencies. Please reload the page and try again.": "Desculpe, foi encontrada alguma inconsist\u00eancia nos dados. Por favor, recarregue a p\u00e1gina e tente novamente.",
    "Sorry, we are unable to process your operation. Please reload the page and try again.": "Desculpe, n\u00e3o foi poss\u00edvel realizar sua opera\u00e7\u00e3o. Por favor, recarregue a p\u00e1gina e tente novamente.",
    "This is the list of available %s. You may choose some by selecting them in the box below and then clicking the \"Choose\" arrow between the two boxes.": "Esta \u00e9 a lista de %s dispon\u00edveis. Voc\u00ea pode escolh\u00ea-los(as) selecionando-os(as) abaixo e clicando na seta \"Escolher\" entre as duas caixas.",
    "This is the list of chosen %s. You may remove some by selecting them in the box below and then clicking the \"Remove\" arrow between the two boxes.": "Esta \u00e9 a lista de %s dispon\u00edveis. Voc\u00ea pode remov\u00ea-los(as) selecionando-os(as) abaixo e clicando na seta \"Remover\" entre as duas caixas.",
    "Today": "Hoje",
    "Tomorrow": "Amanh\u00e3",
    "Type into this box to filter down the list of available %s.": "Digite nessa caixa para filtrar a lista de %s dispon\u00edveis.",
    "Yesterday": "Ontem",
    "You have selected an action, and you haven't made any changes on individual fields. You're probably looking for the Go button rather than the Save button.": "Voc\u00ea selecionou uma a\u00e7\u00e3o, e voc\u00ea n\u00e3o fez altera\u00e7\u00f5es em campos individuais. Voc\u00ea provavelmente est\u00e1 procurando o bot\u00e3o Ir ao inv\u00e9s do bot\u00e3o Salvar.",
    "You have selected an action, but you haven't saved your changes to individual fields yet. Please click OK to save. You'll need to re-run the action.": "Voc\u00ea selecionou uma a\u00e7\u00e3o, mas voc\u00ea n\u00e3o salvou as altera\u00e7\u00f5es de cada campo ainda. Clique em OK para salvar. Voc\u00ea vai precisar executar novamente a a\u00e7\u00e3o.",
    "You have unsaved changes on individual editable fields. If you run an action, your unsaved changes will be lost.": "Voc\u00ea tem altera\u00e7\u00f5es n\u00e3o salvas em campos edit\u00e1veis individuais. Se voc\u00ea executar uma a\u00e7\u00e3o suas altera\u00e7\u00f5es n\u00e3o salvas ser\u00e3o perdidas.",
    "en-US": "pt-BR",
    "mm/dd/yy": "dd/mm/yy",
    "one letter Friday\u0004F": "S",
    "one letter Monday\u0004M": "S",
    "one letter Saturday\u0004S": "S",
    "one letter Sunday\u0004S": "D",
    "one letter Thursday\u0004T": "Q",
    "one letter Tuesday\u0004T": "T",
    "one letter Wednesday\u0004W": "Q"
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
      "%d/%m/%Y %H:%M:%S",
      "%d/%m/%Y %H:%M:%S.%f",
      "%d/%m/%Y %H:%M",
      "%d/%m/%Y",
      "%d/%m/%y %H:%M:%S",
      "%d/%m/%y %H:%M:%S.%f",
      "%d/%m/%y %H:%M",
      "%d/%m/%y",
      "%Y-%m-%d %H:%M:%S",
      "%Y-%m-%d %H:%M:%S.%f",
      "%Y-%m-%d %H:%M",
      "%Y-%m-%d"
    ],
    "DATE_FORMAT": "j \\d\\e F \\d\\e Y",
    "DATE_INPUT_FORMATS": [
      "%d/%m/%Y",
      "%d/%m/%y",
      "%Y-%m-%d"
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

