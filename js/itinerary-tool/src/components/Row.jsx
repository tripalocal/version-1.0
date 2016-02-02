import React from 'react';
import Cell from './Cell.jsx!';

export default class Row extends React.Component {
  constructor(props) {
    super(props);
  }
  render() {
    const fields = Object.keys(this.props.day).map(field =>
      <Cell key={this.props.date + field}
        val={this.props.day[field]}/>
    );
    return (
      <tr>{fields}</tr>
    );
  }
}

export let __hotReload = true;
