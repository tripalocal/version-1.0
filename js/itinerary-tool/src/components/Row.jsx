import React from 'react';
import Cell from './Cell.jsx!';

export default class Row extends React.Component {
  constructor(props) {
    super(props);
  }
  render() {
    const fields = Object.keys(this.props.day).map(field => {
      if (field === 'date') {
        return (
          <td key={this.props.day.date + field}>{this.props.day[field]}</td>
        );
      } else {
        return(
          <Cell key={this.props.day.date + field}
            value={this.props.day[field]}
            type={field}
          />
        );
      }
    });
    return (
      <tr>{fields}</tr>
    );
  }
}

export let __hotReload = true;
