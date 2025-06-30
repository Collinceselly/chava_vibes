// fetch('/navbar.html')
//       .then(response => response.text())
//       .then(html => {
//         document.body.insertAdjacentHTML('afterbegin', html);
//       })
//       .catch(error => console.error('Error loading navbar:', error));


// document.addEventListener('DOMContentLoaded', () => {
//   console.log('Loading navbar...');
//   fetch('/navbar.html')
//     .then(response => {
//       if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
//       return response.text();
//     })
//     .then(html => {
//       console.log('Navbar HTML loaded:', html);
//       const content = document.getElementById('content');
//       if (content) {
//         content.insertAdjacentHTML('beforebegin', html);
//       } else {
//         document.body.insertAdjacentHTML('afterbegin', html);
//       }
//     })
//     .catch(error => console.error('Error loading navbar:', error));
// });



document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM fully loaded, starting navbar load...');
  fetch('/navbar.html')
    .then(response => {
      if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
      return response.text();
    })
    .then(html => {
      console.log('Navbar HTML fetched:', html);
      const content = document.getElementById('content');
      if (content) {
        const navbarHTML = document.createElement('div');
        navbarHTML.innerHTML = html;
        document.body.insertBefore(navbarHTML.firstChild, content);
        console.log('Navbar inserted before content');
      } else {
        console.log('Content div not found, inserting at body start...');
        document.body.insertAdjacentHTML('afterbegin', html);
      }
    })
    .catch(error => console.error('Error loading navbar:', error));
});