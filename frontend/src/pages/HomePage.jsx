import { Box, Typography, Button, Container, Grid, Card, CardContent, Paper, Chip } from '@mui/material'
import { 
  FlightTakeoff, 
  Search, 
  Security, 
  Speed, 
  Hotel, 
  Favorite, 
  TrendingUp,
  Support,
  VerifiedUser,
  LocalOffer,
  ArrowForward
} from '@mui/icons-material'
import { Link as RouterLink } from 'react-router-dom'
import GlobeCard from '../components/GlobeCard'
import './HomePage.css'

const HomePage = () => {
  const features = [
    {
      icon: <Search />,
      title: 'Зручний пошук',
      description: 'Шукайте рейси за містом або кодом аеропорту. Порівнюйте ціни різних авіаліній миттєво.',
    },
    {
      icon: <Security />,
      title: 'Безпечне бронювання',
      description: 'Надійні платежі та захист даних завдяки сучасному шифруванню.',
    },
    {
      icon: <Speed />,
      title: 'Швидко та надійно',
      description: 'Оперативне бронювання з миттєвими підтвердженнями та актуальною наявністю місць.',
    },
    {
      icon: <Hotel />,
      title: 'Готелі',
      description: 'Бронюйте готелі поруч з аеропортами та знаходьте ідеальне проживання для подорожі.',
    },
    {
      icon: <Favorite />,
      title: 'Обране',
      description: 'Зберігайте улюблені рейси та готелі для швидкого доступу до найкращих пропозицій.',
    },
    {
      icon: <TrendingUp />,
      title: 'Найкращі ціни',
      description: 'Порівнюйте ціни від різних авіаліній і готелів та обирайте оптимальні варіанти.',
    }
  ]

  const stats = [
    { number: '500+', label: 'Рейсів щодня' },
    { number: '13', label: 'Готелів' },
    { number: '50+', label: 'Напрямків' },
    { number: '10K+', label: 'Задоволених клієнтів' }
  ]

  return (
    <Box className="home-page-modern">
      {/* Hero Section */}
      <Box className="hero-modern">
        <Container maxWidth="lg">
          <Box className="hero-content-modern">
            <Box className="hero-icon-wrapper">
              <FlightTakeoff className="hero-icon-modern" />
            </Box>
            <Typography variant="h1" className="hero-title-modern">
              Знайдіть ідеальний рейс
            </Typography>
            <Typography variant="h5" className="hero-subtitle-modern">
              Порівнюйте ціни різних авіаліній і бронюйте найкращі пропозиції.
              Ваша подорож починається тут.
            </Typography>
            <Box className="hero-buttons-modern">
              <Button
                component={RouterLink}
                to="/search"
                variant="contained"
                size="large"
                className="hero-button-modern primary"
                endIcon={<ArrowForward />}
              >
                Пошук рейсів
              </Button>
              <Button
                component={RouterLink}
                to="/hotels"
                variant="outlined"
                size="large"
                className="hero-button-modern secondary"
                endIcon={<ArrowForward />}
              >
                Бронювання готелів
              </Button>
            </Box>
            <Box className="hero-badges-modern">
              <Chip 
                icon={<VerifiedUser />} 
                label="Захищені платежі" 
                className="badge-chip-modern"
              />
              <Chip 
                icon={<LocalOffer />} 
                label="Найкращі ціни" 
                className="badge-chip-modern"
              />
              <Chip 
                icon={<Support />} 
                label="Підтримка 24/7" 
                className="badge-chip-modern"
              />
            </Box>
          </Box>
        </Container>
      </Box>

      {/* Stats Section */}
      <Container maxWidth="lg">
        <Box className="stats-section-modern">
          <Grid container spacing={3}>
            {stats.map((stat, index) => (
              <Grid item xs={6} md={3} key={index}>
                <Box className="stat-item-modern">
                  <Typography variant="h2" className="stat-number-modern">
                    {stat.number}
                  </Typography>
                  <Typography variant="body1" className="stat-label-modern">
                    {stat.label}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Container>

      {/* Globe Section */}
      <Container maxWidth="lg" style={{ marginTop: 40 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={7}>
            <GlobeCard title="Глобус перельотів" />
          </Grid>
          <Grid item xs={12} md={5}>
            <Paper style={{ background:'#141414', border:'1px solid rgba(255,152,0,0.1)' }}>
              <Box p={3}>
                <Typography variant="h5" style={{ color:'#fff', fontWeight:700, marginBottom:8 }}>Подорожуйте світом</Typography>
                <Typography variant="body1" style={{ color:'rgba(255,255,255,0.7)' }}>
                  Відкривайте нові напрямки та маршрути. Інтерактивний глобус підсвічує популярні перельоти у нашій чорнo-оранжевій гамі.
                </Typography>
              </Box>
            </Paper>
          </Grid>
        </Grid>
      </Container>

      {/* Features Section */}
      <Container maxWidth="lg" className="features-container-modern">
        <Box className="section-header-modern">
          <Typography variant="h2" className="section-title-modern">
            Чому обирають нас?
          </Typography>
          <Typography variant="body1" className="section-subtitle-modern">
            Ми робимо планування подорожей простим, безпечним і доступним
          </Typography>
        </Box>
        <Grid container spacing={3} className="features-grid-modern">
          {features.map((feature, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card className="feature-card-modern">
                <CardContent className="feature-content-modern">
                  <Box className="feature-icon-modern">
                    {feature.icon}
                  </Box>
                  <Typography variant="h5" className="feature-title-modern" gutterBottom>
                    {feature.title}
                  </Typography>
                  <Typography variant="body1" className="feature-description-modern">
                    {feature.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* CTA Section */}
      <Box className="cta-section-modern">
        <Container maxWidth="lg">
          <Box className="cta-content-modern">
            <Typography variant="h2" className="cta-title-modern">
              Готові розпочати подорож?
            </Typography>
            <Typography variant="h6" className="cta-subtitle-modern">
              Шукайте рейси та готелі просто зараз. Гарантовано вигідні ціни!
            </Typography>
            <Button
              component={RouterLink}
              to="/search"
              variant="contained"
              size="large"
              className="cta-button-modern"
              endIcon={<ArrowForward />}
            >
              Розпочати пошук
            </Button>
          </Box>
        </Container>
      </Box>
    </Box>
  )
}

export default HomePage
