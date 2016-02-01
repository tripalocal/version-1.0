import React from 'react';
import Cell from './Cell.jsx!';

export let __hotReload = true

export default class Row extends React.Component {
  constructor(props) {
    super(props);
  }
  render() {
    const cells = [];
    for (let field in this.props.day) {
      cells.push(<Cell key={this.props.day + field} val={this.props.day[field]}/>);
    }
    return (
      <tr>{cells}</tr>
    );
  }
}