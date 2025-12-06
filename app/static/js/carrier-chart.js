// SIM Carrier Distribution Horizontal Bar Chart using D3.js
(function() {
    'use strict';

    const margin = {top: 20, right: 30, bottom: 40, left: 180};
    const width = 600 - margin.left - margin.right;
    const height = 300 - margin.top - margin.bottom;

    // Create SVG container
    const svg = d3.select('#carrier-chart')
        .append('svg')
        .attr('width', width + margin.left + margin.right)
        .attr('height', height + margin.top + margin.bottom)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    // Carrier colors - matching Croatian operators
    const carrierColors = {
        'Hrvatski Telekom': '#e20074',
        'A1 Hrvatska': '#c40f39',
        'Telemach Hrvatska': '#00b8a9',
        'Unknown': '#9b9b9b'
    };

    // Fetch data and render chart
    fetch('/api/sim-carrier-distribution')
        .then(response => response.json())
        .then(data => {
            if (!data || data.length === 0) {
                d3.select('#carrier-chart')
                    .append('p')
                    .attr('class', 'no-data-message')
                    .text('No carrier data available');
                return;
            }

            // Create scales
            const xScale = d3.scaleLinear()
                .domain([0, d3.max(data, d => d.count)])
                .range([0, width]);

            const yScale = d3.scaleBand()
                .domain(data.map(d => d.carrier))
                .range([0, height])
                .padding(0.2);

            // Add X axis
            svg.append('g')
                .attr('transform', `translate(0,${height})`)
                .call(d3.axisBottom(xScale).ticks(5))
                .style('font-size', '12px');

            // Add Y axis
            svg.append('g')
                .call(d3.axisLeft(yScale))
                .style('font-size', '13px')
                .style('font-weight', '500');

            // Create tooltip
            const tooltip = d3.select('body')
                .append('div')
                .attr('class', 'chart-tooltip')
                .style('opacity', 0);

            // Calculate total for percentages
            const total = d3.sum(data, d => d.count);

            // Add bars
            svg.selectAll('.bar')
                .data(data)
                .enter()
                .append('rect')
                .attr('class', 'bar')
                .attr('x', 0)
                .attr('y', d => yScale(d.carrier))
                .attr('height', yScale.bandwidth())
                .attr('fill', d => carrierColors[d.carrier] || carrierColors['Unknown'])
                .attr('rx', 4)
                .style('cursor', 'pointer')
                .on('mouseenter', function(event, d) {
                    d3.select(this)
                        .transition()
                        .duration(200)
                        .attr('opacity', 0.8);

                    const percentage = ((d.count / total) * 100).toFixed(1);
                    tooltip.transition()
                        .duration(200)
                        .style('opacity', 0.95);
                    tooltip.html(`
                        <strong>${d.carrier}</strong><br/>
                        SIMs: ${d.count}<br/>
                        Share: ${percentage}%
                    `)
                        .style('left', (event.pageX + 10) + 'px')
                        .style('top', (event.pageY - 28) + 'px');
                })
                .on('mouseleave', function() {
                    d3.select(this)
                        .transition()
                        .duration(200)
                        .attr('opacity', 1);

                    tooltip.transition()
                        .duration(500)
                        .style('opacity', 0);
                })
                .attr('width', 0)
                .transition()
                .duration(1000)
                .delay((d, i) => i * 100)
                .attr('width', d => xScale(d.count));

            // Add value labels on bars
            svg.selectAll('.label')
                .data(data)
                .enter()
                .append('text')
                .attr('class', 'bar-label')
                .attr('x', d => xScale(d.count) + 5)
                .attr('y', d => yScale(d.carrier) + yScale.bandwidth() / 2)
                .attr('dy', '0.35em')
                .style('font-size', '13px')
                .style('font-weight', 'bold')
                .style('fill', '#262626')
                .style('opacity', 0)
                .text(d => d.count)
                .transition()
                .duration(1000)
                .delay((d, i) => i * 100 + 500)
                .style('opacity', 1);

            // Add chart title annotation
            svg.append('text')
                .attr('x', width / 2)
                .attr('y', -5)
                .attr('text-anchor', 'middle')
                .style('font-size', '12px')
                .style('fill', '#6b6b6b')
                .text(`Total: ${total} SIMs across ${data.length} carriers`);
        })
        .catch(error => {
            console.error('Error fetching carrier data:', error);
            d3.select('#carrier-chart')
                .append('p')
                .attr('class', 'error-message')
                .text('Error loading chart data');
        });
})();
