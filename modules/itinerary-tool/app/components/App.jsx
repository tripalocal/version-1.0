import React from 'react';
import Bar from './Bar.jsx';
import Table from './Table.jsx';
import NewItemModal from './NewItemModal.jsx';

export default class App extends React.Component {
  constructor(props) {
    super(props);
    // Initialize state
    this.state = {
      showModal: false
    }
    // Bind methods to object context
    this.handleModalOpen = this.handleModalOpen.bind(this);
    this.handleModalClose = this.handleModalClose.bind(this)
  }

  handleModalOpen() {
    this.setState({showModal: true});
  }

  handleModalClose(){
    this.setState({showModal: false});
  }
 
  render() {
    return (
      <div>
        <Bar />
        <Table days={this.props.days} handleModalOpen={this.handleModalOpen} />
        {
          this.state.showModal ? 
          <NewItemModal onClose={this.handleModalClose} /> :
          null
        }
      </div>
    );
  }
}
