import { expect } from 'chai'
import reducer from '../app/reducers.js'

describe('Reducers', () => {
  describe('modal', () => {
    it('should return the initial state', () => {
      expect(
        reducer(undefined, {})
      ).to.eql(
        {
          modal: {date: '', field: '', display: 'NONE'},
          dates: {},
          form: {} 
        }
      )
    })

    it('should handle SHOW_MODAL', () => {
      expect(
        reducer({}, {
          type: 'SHOW_MODAL',
          date: '2016-03-04',
          field: 'experiences',
          setting: 'NEW_ITEM'
        })
      ).to.eql(
        {
        modal: {date: '2016-03-04', field: 'experiences', display: 'NEW_ITEM'},
        dates: {},
        form: {}
        }
      )
    })
  })

  describe('dates', () => {
    it('should return the initial state', () => {
      expect(
        reducer(undefined, {})
      ).to.eql(
        {
          modal: {date: '', field: '', display: 'NONE'},
          dates: {},
          form: {} 
        }
      )
    })

    it('should handle SHOW_SELECT', () => {
    })
  })
})
