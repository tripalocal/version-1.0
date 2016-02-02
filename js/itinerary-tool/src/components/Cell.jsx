import React from 'react';
import Select from 'react-select';

export default class Cell extends React.Component {
  constructor(props) {
    super(props);
    // Initial state
    this.state = {
      editing: false,
      val: this.props.val
    };
    // Bind methods to component
    this.edit = this.edit.bind(this);
    this.finishEdit = this.finishEdit.bind(this);
    this.getOptions = this.getOptions.bind(this);
  }

  render() {
    console.log(this.state.val);
    return(
      <td>
        <Select.Async
          name={this.props.key}
          loadOptions={this.getOptions}
          onFocus={this.edit}
          placeholder={this.props.type}
          onChange={this.finishEdit}
          value={this.state.val}
        />
      </td>
    );
  }

  edit() {
    // Enter edit mode.
    this.setState({
      editing: true
    });
  }

  finishEdit(e) {
    // Exit edit mode and update state.
    e == null ?
    this.setState({editing: false, val: ''}) :
    this.setState({editing: false, val: e.value});
  }

  getOptions(input, callback) {
    // Will be an ajax call.
    setTimeout(() => {
      callback(null, {
        options: TEST_DATA[this.props.type]
      });
    }, 1000);
    // Test data.
    const TEST_DATA = {
      'items' : [
        { value: '1123', label: 'Skiing'},
        { value: '8282', label: 'Explore the jungle'},
        { value: '6624', label: 'Fight club'},
        { value: '43224', label: 'Fishing'}
      ],

      'transport' : [
        { value: '30309', label: 'CX390 MEL to SYD'},
        { value: '12498', label: 'ZX201 MEL to BRI'},
        { value: '3234', label: 'TX203 SYD to NZL'},
        { value: '309', label: 'TT201 SYD to BRI'}
      ],

      'accommodation' : [
        { value: '3029', label: 'Grand Hotel'},
        { value: '20029', label: 'Super Hotel'},
        { value: '19343', label: 'Cool Cottage'}
      ],

      'restaurant' : [
        { value: '430', label: 'Continental breakfast'},
        { value: '143', label: 'Italian lunch'},
        { value: '9343', label: 'Flying lotus'},
        { value: '1343', label: 'Asian delight'}
      ]
    };
  }
}


export let __hotReload = true;
