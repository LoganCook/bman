angular.module('mereUI').component('casDropdowns', {
  template: `
  <form class="form-inline">
    <div class="form-group">
        <label for="level1" style="width:auto">Level 1</label>
        <select id="level1" ng-options="item.name for item in ::$ctrl.levelData[0] track by item.id" ng-model="$ctrl.selected[0]"></select>
    </div>
    <div class="form-group" ng-repeat="level in ::$ctrl.levels" ng-show="$ctrl.canShow({{level}})">
      <label for="level{{level}}">Level {{level + 1}}</label>
      <select id="level{{level}}" ng-options="item.name for item in $ctrl.levelData[level][$ctrl.selected[level-1].id] track by item.id" ng-model="$ctrl.selected[level]"></select>
    </div>
   </form>
  `,
  bindings: {
    levelData: '<',
    setSpy: '&'
  },
  controller: function CompController () {
    function getSelected() {
      var lvl = 0, ids = [];
      while (ctrl.selected[lvl]) {
        ids.push(ctrl.selected[lvl++]['name']);
      }
      return ids;
    }

    var ctrl = this;
    ctrl.levels = [];
    ctrl.selected = [];
    for (var i = 1; i < ctrl.levelData.length; i++) {
      ctrl.levels.push(i);
    }
    console.log(ctrl.levelData);
    ctrl.setSpy({spy: getSelected});
    ctrl.canShow = function(lvl) {
      var parentLevel = parseInt(lvl) - 1;
      if (angular.isDefined(ctrl.selected[parentLevel]) && ctrl.selected[parentLevel] !== null) {
        return ctrl.selected[parentLevel]['id'] in ctrl.levelData[lvl];
      } else {
        return false;
      }
    };
  }
});
