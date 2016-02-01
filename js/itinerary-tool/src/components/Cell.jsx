import React from 'react';
export let __hotReload = true
export default class Cell extends React.Component {
  constructor(props) {
    super(props);

    // Track `editing` state.
    this.state = {
      editing: false
    };
  }

  render() {
    if (this.state.editing) {
      return this.renderEdit();
    }
    return this.renderCell();
  }

  renderCell = () => {
    return (
      <td onClick={this.edit}>{this.props.val}</td>
    );
  };

  renderEdit = () => {
    return <input type="text"
      autoFocus={true}
      defaultValue={this.props.val}
      onBlur={this.finishEdit}
      onKeyPress={this.checkEnter} />;
  };

  edit = () => {
    //Enter edit mode.
    this.setState({
      editing: true
    });
  };

  checkEnter = (e) => {
    if (e.key === 'Enter') {
      this.finishEdit(e);
    }
  };

  finishEdit = (e) => {
    const value = e.target.value;

    if (this.props.onEdit && value.trim()) {
      this.props.onEdit(value);
      this.setState({
        editing: false
      });
    }
  };
}