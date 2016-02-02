import React from 'react';

export default class Cell extends React.Component {
  constructor(props) {
    super(props);
    // Initial state
    this.state = {
      editing: false,
      val: this.props.val
    };
    // Bind methods to component
    this.renderCell = this.renderCell.bind(this);
    this.renderEdit = this.renderEdit.bind(this);
    this.edit = this.edit.bind(this);
    this.checkEnter = this.checkEnter.bind(this);
    this.finishEdit = this.finishEdit.bind(this);
  }

  render() {
    if (this.state.editing) {
      return this.renderEdit();
    }
    return this.renderCell();
  }

  renderCell() {
    return (
      <td onClick={this.edit}>{this.state.val}</td>
    );
  }

  renderEdit() {
    return (
      <td>
        <input type="text"
          autoFocus={true}
          defaultValue={this.state.val}
          onBlur={this.finishEdit}
          onKeyPress={this.checkEnter} />
      </td>
    );
  }

  edit() {
    //Enter edit mode.
    this.setState({
      editing: true
    });
  }

  checkEnter(e) {
    if (e.key === 'Enter') {
      this.finishEdit(e);
    }
  };

  finishEdit(e) {
    const value = e.target.value;

    if (value.trim()) {
      this.setState({
        editing: false,
        val: value
      });
    } else {
      this.setState({
        editing: false
      });
    };
  };
}

export let __hotReload = true;
