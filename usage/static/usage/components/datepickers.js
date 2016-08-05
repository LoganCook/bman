function dateToTimestamp(d, end) {
  end = end | false;
  // Get timestamp of a local time
  if (d instanceof Date) {
    if (end) {
      d.setHours(23);
      d.setMinutes(59);
      d.setSeconds(59);
    } else {
      d.setHours(0);
      d.setMinutes(0);
      d.setSeconds(0);
    }
    return parseInt(d.getTime() / 1000, 10);
  } else {
    throw new TypeError("Only Date type is acceptable");
  }
}

angular.module('mereUI').component('datePickers', {
  template: `
    <div ng-repeat="picker in ::$ctrl.pickers">
      <date-picker-uib picker="picker"></date-picker-uib>
    </div>
  `,
  bindings: {
    pickers: '<',
    setSpy: '&'
  },
  controller: function () {
    var ctrl = this;

    function collect() {
        return [dateToTimestamp(ctrl.pickers[0].date),
                dateToTimestamp(ctrl.pickers[1].date, true)];
    };
    ctrl.setSpy({spy: collect});
  }
}).component('datePickerUib', {
  template: `
    <div ng-class="$ctrl.picker.class">
        <p>{{$ctrl.picker.title}}</p>
        <p class="input-group">
            <input type="text" class="form-control" uib-datepicker-popup="{{$ctrl.picker.format}}"
             ng-model="$ctrl.picker.date" is-open="$ctrl.opened" showWeeks="false" datepicker-options="$ctrl.options" ng-required="true"/>
            <span class="input-group-btn">
                <button type="button" class="btn btn-default" ng-click="$ctrl.show()"><i class="glyphicon glyphicon-calendar"></i></button>
            </span>
        </p>
        <span ng-show="$ctrl.picker.date.$error.invalidDate">Invalid start date.</span>
    </div>
  `,
  bindings: {
    picker: '<'
  },
  controller: function () {
    var defaults = {
        'class': 'col-md-6',
        'format': 'dd/MM/yyyy'
    };

    var ctrl = this;
    angular.forEach(defaults, function(value, key) {
        if (!(key in ctrl.picker)) {
            ctrl.picker[key] = value;
        }
    });

    ctrl.options = {
      maxDate: new Date()
    };
    if ('minDate' in ctrl.picker) {
      ctrl.options['minDate'] = ctrl.picker['minDate'];
    }

    ctrl.opened = false;
    ctrl.show = function() {
      ctrl.opened = true;
    };
  }
});
