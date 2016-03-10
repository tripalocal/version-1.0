import { expect } from 'chai'
import * as actions from '../app/actions'

describe('Actions', () => {
  it('should create an action SHOW_MODAL', () => {
    const date = '2016-03-09'
    const field = 'restaurant'
    const setting = 'NEW_ITEM'
    const expectedAction = {
      type: 'SHOW_MODAL',
      date,
      field,
      setting
    }
    expect(actions.showModal(date, field, setting)).to.eql(expectedAction)
  })

  it('should create an action SHOW_SELECT', () => {
    const date = '2016-03-09'
    const field = 'restaurant'
    const setting = 'EDIT'
    const expectedAction = {
      type: 'SHOW_SELECT',
      date,
      field,
      setting
    }
    expect(actions.showSelect(date, field, setting)).to.eql(expectedAction)
  })
})
