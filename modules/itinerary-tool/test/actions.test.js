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

  it('should create an action ADD_DATE', () => {
    const date = '2016-03-09'
    const city = 'melbourne'
    const expectedActionBefore = {
      type: 'ADD_DATE',
      city,
      date: '2016-03-08'
    }
    const expectedActionAfter = {
      type: 'ADD_DATE',
      city,
      date: '2016-03-10'
    }
    expect(actions.addDate(date, city, 'BEFORE')).to.eql(expectedActionBefore)
    expect(actions.addDate(date, city, 'AFTER')).to.eql(expectedActionAfter)
  })
})
