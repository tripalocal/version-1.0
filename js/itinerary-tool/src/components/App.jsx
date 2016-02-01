import React from 'react';
import Bar from './Bar.jsx!';
import Table from './Table.jsx!'

export default class App extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {

    return (
      <div>
        <Bar />
        <Table days={this.props.days} />
      </div>
    );
  }
}
