import React from 'react';
import {ModalContainer, ModalDialog} from 'react-modal-dialog';

export default class NewItemModal extends React.Component {
  constructor(props) {
    super(props);
  }
  
  render() {
    return (
      <ModalContainer onClose={this.props.onClose}>
        <ModalDialog onClose={this.props.onClose}>
          <h1>New Item</h1>
        </ModalDialog>
      </ModalContainer>
    );
  }
}


export let __hotReload = true;
