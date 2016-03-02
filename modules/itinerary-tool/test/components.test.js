import { expect } from 'chai'
import TestUtils from 'react-addons-test-utils'
import React from 'react'
import Table from '../app/components/Table'
import Modal from '../app/components/Modal'

function setupTable() {
  let props = {
    dates: {
    '2016-03-01': {
      city: 'melbourne',
      experiences: {
        items: ['cool activity', 'another one'],
        host: '',
        display: 'NORMAL'
      },
      transport: {
        items: [],
        host: 'Guy',
        display: 'NORMAL'
      },
      accommodation: {
        items: ['Hilton'],
        host: 'Guy',
        display: 'NORMAL'
      },
      restaurants: {
        items: ['Food Inc.'],
        host: 'Person',
        display: 'EDIT'
      }
    },
    '2016-03-02': {
      city: 'melbourne',
      experiences: {
        items: ['cool activity', 'another one'],
        host: '',
        display: 'NORMAL'
      },
      transport: {
        items: [],
        host: 'Guy',
        display: 'NORMAL'
      },
      accommodation: {
        items: ['Hilton'],
        host: 'Guy',
        display: 'NORMAL'
      },
      restaurants: {
        items: ['Food Inc.'],
        host: 'Person',
        display: 'EDIT'
      }
    }
  }}
  let renderer = TestUtils.createRenderer()
  renderer.render(<Table {...props} />)
  let output = renderer.getRenderOutput()

  return {
    props,
    output,
    renderer
  }
}

function setupModal(setting) {
  let props = {
    setting: setting,
    handleClose: null,
    handleSubmit: null 
  }
  let renderer = TestUtils.createRenderer()
  renderer.render(<Modal {...props} />)
  let output = renderer.getRenderOutput()

  return {
    props,
    output,
    renderer
  }
}

describe('Components', () => {
  describe('table', () => {
    it('should render correctly', () => {
      const { output } = setupTable()

      expect(output.type).to.equal('table')
      expect(output.props.className).to.equal('table')

      let [ thead, tbody ] = output.props.children
      expect(thead.type).to.equal('thead')
      expect(tbody.type).to.equal('tbody')
    })

  })

  describe('modal', () => {
    it('should render NewItemForm if setting is NEW_ITEM', () => {
      const { output } = setupModal('NEW_ITEM')
      expect(output.type).to.eql('ModalContainer')
    })

    it('should render AssignHostForm if setting is ASSIGN_HOST', () => {
      const { output } = setupModal('ASSIGN_HOST')
      expect(output.type).to.eql('ModalContainer')
    })
  })
})
