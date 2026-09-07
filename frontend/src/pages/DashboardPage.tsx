import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert,
  Chip,
  Paper,
  Button,
} from '@mui/material';
import { useUserProfile, useMatchHistory, useDifficultMatchups, useChampionRecommendations } from '../hooks/useApi';
import PageHeader from '../components/PageHeader';

const DashboardPage: React.FC = () => {
  const { isLoading: userLoading, error: userError } = useUserProfile();
  const { data: matches, isLoading: matchesLoading, error: matchesError } = useMatchHistory();
  const { data: difficultMatchups, isLoading: matchupsLoading, error: matchupsError } = useDifficultMatchups();
  const { data: recommendations, isLoading: recommendationsLoading, error: recommendationsError } = useChampionRecommendations();

  const isLoading = userLoading || matchesLoading || matchupsLoading || recommendationsLoading;

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress size={60} />
        <Typography sx={{ ml: 2 }}>Loading your League data...</Typography>
      </Box>
    );
  }

  // Show errors if any
  if (userError || matchesError || matchupsError || recommendationsError) {
    return (
      <Box>
        <Alert severity="error">
          Error loading data: {userError?.message || matchesError?.message || matchupsError?.message || recommendationsError?.message}
        </Alert>
        <Button 
          variant="contained" 
          onClick={() => window.location.reload()} 
          sx={{ mt: 2 }}
        >
          Retry
        </Button>
      </Box>
    );
  }


  const difficultMatchupsData = difficultMatchups?.slice(0, 5).map((matchup: any) => ({
    champion: matchup.champion,
    winRate: matchup.win_rate,
    games: matchup.games_played
  }));

  return (
    <Box>
      <PageHeader
        title="Dashboard"
        description="Your current record, and the matchups costing you games."
      />

      <Grid container spacing={3}>
        {/* Recent Performance */}
        {/* Recent Performance bar chart removed per requirements */}

        {/* Quick Stats */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Stats
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                  <Typography variant="body2" color="text.secondary">
                    Total Matches
                  </Typography>
                  <Typography variant="h4">
                    {matches?.length || 0}
                  </Typography>
                </Paper>
                <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                  <Typography variant="body2" color="text.secondary">
                    Difficult Matchups
                  </Typography>
                  <Typography variant="h4">
                    {difficultMatchups?.length || 0}
                  </Typography>
                </Paper>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Most Difficult Matchups */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Most Difficult Matchups
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {difficultMatchupsData?.map((matchup: any) => (
                  <Box
                    key={matchup.champion}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      p: 1
                    }}
                  >
                    <Typography variant="body1">
                      {matchup.champion}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <Chip
                        label={`${matchup.winRate.toFixed(1)}%`}
                        size="small"
                        color={matchup.winRate < 40 ? 'error' : matchup.winRate < 50 ? 'warning' : 'success'}
                      />
                      <Typography variant="body2" color="text.secondary">
                        {matchup.games} games
                      </Typography>
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Recommended Champions */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Recommended Champions
              </Typography>
              <Grid container spacing={2}>
                {recommendations?.slice(0, 4).map((rec: any) => (
                  <Grid item xs={12} sm={6} md={3} key={rec.champion}>
                    <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                      <Typography variant="h6" gutterBottom>
                        {rec.champion}
                      </Typography>
                      <Chip
                        label={`${rec.counter_win_rate.toFixed(1)}% vs counters`}
                        size="small"
                        color="primary"
                        sx={{ mt: 1 }}
                      />
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {rec.reason}
                      </Typography>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default DashboardPage;