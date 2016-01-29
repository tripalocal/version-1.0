var React = require('react');
var ReactDOM = require('react-dom');

var SettingBar = React.createClass({
  render: function() {
    return (
      <div className="bar">
      </div>
    )
  }
})

var DayRow = React.createClass({
  render: function() {
    return (
      <tr>
        <td>{this.props.day.date}</td>
        <td>{this.props.day.items}</td>
      </tr>
    );
  }
});

var DayTable = React.createClass({
  render: function() {
    var rows = [];
    this.props.days.forEach(function(day) {
      rows.push(<DayRow day={day} key={day.date} />);
    })
    return (
      <table className="table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Activities</th>
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
  {date: '2016-02-01', items: 'Lunching, Breathing, Rafting'},
  {date: '2016-02-02', items: 'Eating, Breaking, Laughing'},
  {date: '2016-02-03', items: 'Running, Jumping, Painting'},
]

ReactDOM.render(
  <ItineraryTool days={DAYS} />,
  document.getElementById('container')
)
