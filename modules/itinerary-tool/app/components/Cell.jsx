import React from 'react';
import Select from 'react-select';

export default class Cell extends React.Component {
  constructor(props) {
    super(props);
    // Initialize state
    this.state = {
      value: [{value: this.props.value, label: this.props.value}],
    };
    // Bind methods to object context
    this.renderOption = this.renderOption.bind(this);
    this.renderNewItemLink = this.renderNewItemLink.bind(this);
    this.getOptions = this.getOptions.bind(this);
    this.handleChange = this.handleChange.bind(this);
  }

  render() {
    return(
      <td>
        <Select.Async
          loadOptions={this.getOptions}
          optionRenderer={this.renderOption}
          placeholder={this.props.type}
          onChange={this.handleChange}
          value={this.state.value}
          multi={true}
          clearable={false}
          valueKey="value"
          labelKey="label"
        />
      </td>
    );
  }

  handleChange(value) {
    this.setState({ value });
  }

  renderOption(option) {
    return <span>{option.label} {option.link}</span>;
  }

  renderNewItemLink() {
    return <a style={{ marginLeft: 5  }} href="#" onClick={this.props.handleModalOpen}>+ Add</a>;
  }

  getOptions(input, callback) {
    // Test data.
    const TEST_DATA = {
      'items' : [
        { value: '1123', label: 'Skiing'},
        { value: '8282', label: 'Explore the jungle'},
        { value: '6624', label: 'Fight club'},
        { value: '43224', label: 'Fishing'},
        { value: '1245, 145, 12', label: 'Exploring, Jumping, Dancing' }
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
    // Will be an ajax call.
    setTimeout(() => {
      const options = TEST_DATA[this.props.type];
      options.push({
        value: 'new',
        label: 'New item',
        link: this.renderNewItemLink(),
        disabled: true
      })
      callback(null, {
        options: options 
      });
    }, 1000);

  }
}

