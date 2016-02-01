var React = require('react');
var ReactDOM = require('react-dom');
var Select = require('react-select');

var SettingBar = React.createClass({
  render: function() {
    return (
      <div className="bar">
      </div>
    )
  }
})

var DayCell = React.createClass({
  render: function() {
    return (
      <td></td>
    )
  }
})

var DayRow = React.createClass({
  render: function() {
    var cells = [];
    for (var key in this.props.day) {
      if (this.props.day.hasOwnKey(key)) {
        cells.push(<DayCell val={day}/>);
      }
    }
    return (
      <tr>{cells}</tr>
    );
  }
});

var DayTable = React.createClass({
  render: function() {
    var rows = [];
    this.props.days.forEach(function(day) {
      rows.push(<DayRow day={day} />);
    })
    return (
      <table className="table table-striped">
        <thead>
          <tr>
            <th>Date</th>
            <th>Activities</th>
            <th>Transport</th>
            <th>Accommodation</th>
            <th>Restaurant</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    );
  }
})

var ItineraryTool = React.createClass({
  render: function() {
    return (
      <div>
        <SettingBar />
        <DayTable days={this.props.days} />
      </div>
    );
  }
})


// TEST DATA
var DAYS = [
  {date: '2016-02-01', items: 'Lunching, Breathing, Rafting', transport: 'CX992', accommodation: 'Melbourne 4Star', restaurant: 'Continental breakfast'},
  {date: '2016-02-02', items: 'Eating, Breaking, Laughing', transport: 'Bus Ride', accommodation: 'Hilton 5star', restaurant: 'Great breakfast, lunch, dinner'},
  {date: '2016-02-03', items: 'Running, Jumping, Painting', transport: 'Airport transfer', accommodation: 'Cool Cottage', restaurant: ''},
]

ReactDOM.render(
  <ItineraryTool days={DAYS} />,
  document.getElementById('container')
)
