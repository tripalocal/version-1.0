import React from 'react';
import Row from './Row.jsx!';


export default class Table extends React.Component {
  constructor(props) {
    super(props);
  }
  render() {
    const days = this.props.days.map(day => <Row day={day} key={day.date} />);
    return (
      <table className="table table-striped">
        <thead>
          <tr>
            <th>Date</th>
            <th>Activities</th>
            <th>Transport</th>
            <th>Accommodation</th>
            <th>Restaurants</th>
          </tr>
        </thead>
        <tbody>
          {days}
        </tbody>
      </table>
    );
  }
}

export let __hotReload = true;
