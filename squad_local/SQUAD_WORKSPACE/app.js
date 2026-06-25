// archivo test.js
describe('Mi función', () => {
  it('debe devolver true', () => {
    cy.visit('/mi-url')
    cy.get('h1').should('contain', 'Hola mundo!')
  });
});
