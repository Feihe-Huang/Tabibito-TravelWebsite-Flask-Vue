<template>
  <div class="one" id="chart"></div>

</template>

<script>
import * as echarts from 'echarts';

export default {
  mounted() {
      // 使用JavaScript将Pyecharts图表嵌入到容器中
      const chartContainer = document.getElementById("chart");
      chartContainer.innerHTML = '<iframe src="../../../dist/bar3d_punch_card.html" frameborder="0" style="width:100%;height:500px;"></iframe>';
  },}

</script>

<style>
</style>
